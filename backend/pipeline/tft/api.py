import asyncio
import json
import pandas as pd

from pantheon import pantheon

from utils.configuration import settings
from utils.logger import logging
from utils import utils

API_KEY = settings.api_key
ASSETS_DIR = settings.assets_dir
SERVER = settings.server
MAX_COUNT = settings.max_count


def requestsLog(url, status, headers):
    logging.info(f'status:{status} {url}')
    logging.debug(headers)


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
        data = await panth.get_tft_matchlist(puuid, count=count)
        return data
    except Exception as e:
        logging.error(e)


async def getTFTRecentMatches(puuid, uniq_matches_id=[]):
    try:
        matchlist = await getTFTRecentMatchlist(puuid)
        # Get only unique new matches from left hand side
        new_matchlist = set(matchlist) - set(uniq_matches_id)
        logging.info(f'Fetching ** {len(new_matchlist)} ** new matches')

        tasks = [panth.get_tft_match(match)
                 for match in new_matchlist]
        return await asyncio.gather(*tasks)
    except Exception as e:
        logging.error(e)


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


def get_league(league='challengers'):
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

    loop = asyncio.get_event_loop()

    summoners = loop.run_until_complete(getTFTLeagueFunc())
    utils.write_asset_json(summoners, filename=SERVER + '_' + league)

    summoners_league = json.loads('[]')

    for _, summoner in enumerate(summoners['entries'][:]):
        summoner_detail = loop.run_until_complete(
            getTFT_Summoner(summoner['summonerId']))
        if summoner_detail != None:
            summoners_league.append(summoner_detail)

    utils.write_asset_json(summoners_league, filename='summoners_' + SERVER + '_' + league)

    summoners_league_df = pd.json_normalize(summoners_league)
    summoners_df = pd.json_normalize(summoners['entries'])

    return summoners_league_df.merge(
        summoners_df, left_on='id', right_on='summonerId')
