import argparse
import asyncio
import collections

import json
from typing import Dict, List

import pandas as pd
from pandas import DataFrame

from pymongo import MongoClient

from pantheon import pantheon

from utils.configuration import settings
from utils.parse_config import ConfigParser
from utils.logger import logging
from utils.utils import *

# LOAD_NEW: bool = False
ASSETS_DIR: str = settings.assets_dir
API_KEY: str = settings.api_key
# Default global vars
# SERVER = 'na1'  # ['euw1', 'na1', 'kr', 'oc1']
# LEAGUE = 'challengers'  # ['challengers', 'grandmasters']

MAX_COUNT: int = 30


def requestsLog(url, status, headers):
    logging.info(f'status:{status} {url}')
    logging.debug(headers)


async def start_tft_fetch(load_new: bool, server: str, league: str, max_count: int
                          ):
    LOAD_NEW: bool = load_new
    SERVER: str = server
    LEAGUE: str = league
    MAX_COUNT: int = max_count

    client = MongoClient(settings.db_uri)
    db = client[settings.db_name]

    # create Patheon object to 1 server API key
    panth = pantheon.Pantheon(
        SERVER, API_KEY, requests_logging_function=requestsLog, debug=True)

    async def getSummonerId(name):
        try:
            data = await panth.get_tft_summoner_by_name(name)
            return (data['id'], data['accountId'], data['puuid'])
        except Exception as e:
            logging.error(e)

    async def getTFTRecentMatchlist(puuid, count=MAX_COUNT):
        try:
            data: List[str] = await panth.get_tft_matchlist(puuid, count=count)
            return data
        except Exception as e:
            logging.error(e)
            return []

    async def getTFTRecentMatches(puuid, uniq_matches_id=[]):
        try:
            matchlist = await getTFTRecentMatchlist(puuid)
            # Get only unique new matches from left hand side
            new_matchlist: set = set(matchlist) - set(uniq_matches_id)
            logging.info(f'Fetching ** {len(new_matchlist)} ** new matches')

            tasks: list = [panth.get_tft_match(match)
                           for match in new_matchlist]
            # Extend new matches
            uniq_matches_id.extend(new_matchlist)

            matches: tuple = await asyncio.gather(*tasks)

            return matches if matches is not None else [], uniq_matches_id
        except Exception as e:
            logging.error(e)
            return [], uniq_matches_id

    async def getTFTChallengerLeague():
        try:
            data = await panth.get_tft_challenger_league()
            return data
        except Exception as e:
            logging.error(e)

    async def getTFTGrandmasterLeague():
        try:
            data = await panth.get_tft_grandmaster_league()
            return data
        except Exception as e:
            logging.error(e)

    async def getTFTMasterLeague():
        try:
            data = await panth.get_tft_master_league()
            return data
        except Exception as e:
            logging.error(e)

    async def getTFT_Summoner(summonerId):
        try:
            data = await panth.get_tft_summoner(summonerId)
            return data
        except Exception as e:
            logging.error(e)

    async def get_league(league='challengers'):
        """Get league's summoners details.

        Args:
            league (str, optional): TFT league. Defaults to 'challengers'.

        Returns:
            Dataframe: Dataframe of league's summoners details.
            LeagueListDTO
                Name 	Data Type 	Description
                leagueId 	string 	
                entries 	List[LeagueItemDTO] 	
                tier 	string 	
                name 	string 	
                queue 	string 	
                    LeagueItemDTO
                        Name 	Data Type 	Description
                        freshBlood 	boolean 	
                        wins 	int 	First placement.
                        summonerName 	string 	
                        miniSeries 	MiniSeriesDTO 	
                        inactive 	boolean 	
                        veteran 	boolean 	
                        hotStreak 	boolean 	
                        rank 	string 	
                        leaguePoints 	int 	
                        losses 	int 	Second through eighth placement.
                        summonerId 	string 	Player's encrypted summonerId.
                            MiniSeriesDTO
                                Name 	Data Type 	Description
                                losses 	int 	
                                progress 	string 	
                                target 	int 	
                                wins 	int 
        """
        match league:
            case 'challengers':
                getTFTLeagueFunc = getTFTChallengerLeague
            case 'grandmasters':
                getTFTLeagueFunc = getTFTGrandmasterLeague
            case 'masters':
                getTFTLeagueFunc = getTFTMasterLeague
            case _:
                # 0 is the default case if x is not found
                getTFTLeagueFunc = getTFTChallengerLeague

        summoners = await getTFTLeagueFunc()

        summoners_league: List = json.loads('[]')
        for _, summoner in enumerate(summoners['entries'][:]):
            summoner_detail = await getTFT_Summoner(summoner['summonerId'])
            if summoner_detail != None:
                summoners_league.append(summoner_detail)

        summoners_league_df = pd.json_normalize(summoners_league)
        summoners_df = pd.json_normalize(summoners['entries'])

        return summoners_league_df.merge(
            summoners_df, left_on='id', right_on='summonerId')

    # *** Start *** #
    logging.info(
        f'*** Starting SERVER: {SERVER}, LEAGUE: {LEAGUE}, MAX_COUNT: ** {MAX_COUNT} ** run. ***')

    summoners_collection = db[f'{SERVER}_{LEAGUE}_summoners']
    if LOAD_NEW:
        summoners_df: DataFrame = await get_league(league=LEAGUE)
        summoners_df: DataFrame = summoners_df.rename(columns={'id': '_id'})
        summoners_collection.drop()
        summoners_collection.insert_many(
            summoners_df.to_dict('records'), ordered=False)
    else:  # Read cached matches id
        summoners_df = pd.DataFrame(list(summoners_collection.find()))

    logging.info(
        f'Loading for ** {len(summoners_df.index)} ** {"new" if LOAD_NEW else "cached"} summoners.')

    # Get all unique matches_id from assets dir
    matches_asset: list = load_matches_db(collection=db[SERVER + '_' + 'matches_detail'], select={'metadata.match_id': 1})

    matches_id: list = [match['metadata']['match_id']
                        for match in matches_asset]
    seen: set = set()
    uniq_matches_id: list = [
        x for x in matches_id if x not in seen and not seen.add(x)]
    del matches_asset
    logging.info(f'Loaded ** {len(uniq_matches_id)} ** matches.')

    # For each summoners, get MAX_COUNT recent matches. Extend if any new.
    new_counter = 0
    for _, summoner in summoners_df.iterrows():
        matches_detail, uniq_matches_id = await getTFTRecentMatches(summoner['puuid'], uniq_matches_id=uniq_matches_id)
        if matches_detail:
            new_counter += len(matches_detail)

            # db unique id
            for match in matches_detail:
                match['_id'] = match['metadata']['match_id']

            insert_collection_db(
                matches_detail, collection=db[SERVER + '_' + 'matches_detail'])

    client.close()

    return [f'new_counter: ** {new_counter} ** new matches done.\n',
            f'Number of summoners: ** {len(summoners_df.index)} **.\n'
            f'*** End loading from {SERVER}_{LEAGUE} done. ***\n']


# Main #
async def main(config: ConfigParser) -> None:
    """Get matches from RIOT API server. Fetching from different regions asynchronously. **Do not run from same region asynchronous.

    Args:
        config (ConfigParser): Config parameters
    """
    servers: str = config['servers']
    load_new: bool = config["load_new"]
    league: str = config["league"]
    max_count: int = config["max_count"]
    tasks = [asyncio.create_task(start_tft_fetch(
        load_new=load_new, server=server, league=league, max_count=max_count)) for server in servers]

    # Run tasks asynchronously with timeout in 3000s
    done, pending = await asyncio.wait(tasks, timeout=4600, return_when=asyncio.ALL_COMPLETED)
    logging.info(f'Done task count: {len(done)}')
    logging.info(f'Pending task count: {len(pending)}')

    for done_task in done:
        if not done_task.exception():
            logging.info(''.join(done_task.result()))
        else:
            logging.error("Request got an exception",
                          exc_info=done_task.exception())
    for pending_task in pending:
        pending_task.print_stack()
    # await asyncio.create_task(start_tft_fetch(config))


if __name__ == '__main__':
    args = argparse.ArgumentParser(description='TFT API matches scraper')
    args.add_argument('-c', '--config', default=None, type=str,
                      help='config file path (default: None)')
    # custom cli options to modify configuration from default values given in json file.
    CustomArgs = collections.namedtuple('CustomArgs', 'flags type target')
    options = [
        CustomArgs(['-n', '--load_new'], type=bool,
                   target='load_new'),
        CustomArgs(['-s', '--servers'], type=str,
                   target='servers'),
        CustomArgs(['-l', '--league'], type=str,
                   target='league'),
        CustomArgs(['-m', '--max_count'], type=int,
                   target='max_count'),
    ]
    config = ConfigParser.from_args(args, options)

    asyncio.run(main(config))
