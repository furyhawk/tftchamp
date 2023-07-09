#!/usr/bin/env python
# coding: utf-8

import argparse
import asyncio
import collections
from datetime import date, datetime, timedelta

from tft.api import *
from utils.parse_config import ConfigParser
from utils.logger import logging
from utils.utils import *
from utils.configuration import settings
import os.path
from typing import List

import pandas as pd

from datetime import date, datetime, timedelta

# # Config
ASSETS_DIR: str = settings.assets_dir
TARGETNAME: str = settings.targetname  # 'placement'


def process_matches(df) -> List:
    matches_array = []

    for match_row in df:
        match_id = match_row['metadata']['match_id']

        for participant in match_row['info']['participants']:
            match = {}
            match['match_id'] = match_id
            # match['level'] = participant['level']
            match['placement'] = participant['placement']
            # match['players_eliminated'] = participant['players_eliminated']
            # match['total_damage_to_players'] = participant['total_damage_to_players']

            for augment_index, augment in enumerate(participant['augments']):
                # if augment == 'TFT7_Augment_GuildLootHR':
                #     augment = 'TFT7_Augment_BandOfThieves1'
                match[f'augment{augment_index}'] = augment

            for _, trait in enumerate(participant['traits']):
                match[f'{trait["name"]}'] = trait["tier_current"]

            for _, unit in enumerate(participant['units']):
                match[f'{unit["character_id"]}'] = unit["tier"]
                match['TFT7_TrainerDragon_item1'] = 'None'
                match['TFT7_TrainerDragon_item2'] = 'None'
                for item_index, item in enumerate(unit['itemNames']):
                    match[f'{unit["character_id"]}_item{item_index}'] = item.split(
                        '_')[-1]

            matches_array.append(match)

    return matches_array


def reorder_df_col(df):
    fixed_cols = ['placement', 'match_id',
                  'augment0', 'augment1', 'augment2']
    all_cols = df.columns
    to_sort_cols = list(set(all_cols) - set(fixed_cols))

    return df.reindex(columns=fixed_cols + sorted(to_sort_cols))


async def start_tft_data_egress(server: str, league: str, latest_release: str, ranked_id: int, patch: str):

    SERVER: str = server
    LEAGUE: str = league
    LATEST_RELEASE: str = latest_release
    RANKED_ID: int = ranked_id    # 1090 normal game 1100 ranked game
    PATCH: date = date.fromisoformat(patch)
    THREEDAY: datetime = (
        datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")

    summoners_df: pd.DataFrame = pd.read_pickle(os.path.join(
        ASSETS_DIR, f'{SERVER}_{LEAGUE}_summoners.pickle'))
    logging.info(
        f'# Starting {SERVER}_{LEAGUE}_{LATEST_RELEASE}_{PATCH} loading.')

    # # Load unique matches id
    # Get all unique matches_id from assets dir
    matches_asset = load_matches(summoners_df, server=SERVER)
    matches_id = [match['metadata']['match_id'] for match in matches_asset]
    seen = set()
    uniq_matches_id = [
        x for x in matches_id if x not in seen and not seen.add(x)]

    logging.info(f'uniq_matches_id: {len(uniq_matches_id)}')
    logging.info(f'matches_asset: {len(matches_asset)}')

    # Filter for unique matches
    seen = set()
    seen_add = seen.add
    uniq_matches = [x for x in matches_asset if x['metadata']['match_id']
                    not in seen and not seen_add(x['metadata']['match_id'])]

    logging.info(f'uniq_matches: {len(uniq_matches)}')

    # ## Filter by LATEST_RELEASE version and RANKED_ID game.
    latest_matches = [match for match in uniq_matches if (LATEST_RELEASE in match['info']['game_version']) and (
        RANKED_ID == match['info']['queue_id'])]
    # Since last patch matches
    latest_patch_matches = [match for match in uniq_matches if (LATEST_RELEASE in match['info']['game_version'])
                            and (PATCH <= date.fromtimestamp(match['info']['game_datetime']/1000.0))]
    # Last 3 days matches
    latest_3d_matches = [match for match in uniq_matches if (LATEST_RELEASE in match['info']['game_version'])
                         and ((datetime.now() - timedelta(days=3)) <= datetime.fromtimestamp(match['info']['game_datetime']/1000.0))]

    logging.info(f'latest_matches: {len(latest_matches)}')
    logging.info(f'latest_patch_matches: {len(latest_patch_matches)}')
    logging.info(f'latest_3d_matches: {len(latest_3d_matches)}')

    # # Process api details to datasets rows
    matches_array = process_matches(latest_matches)
    matches_patch_array = process_matches(latest_patch_matches)
    matches_3d_array = process_matches(latest_3d_matches)

    # Normalize dict to dataframe
    matches_league_df = pd.json_normalize(matches_array)
    matches_league_patch_df = pd.json_normalize(matches_patch_array)
    matches_league_3d_df = pd.json_normalize(matches_3d_array)

    # ## Sort and reorder columns
    matches_league_df = reorder_df_col(matches_league_df)
    matches_league_patch_df = reorder_df_col(matches_league_patch_df)
    matches_league_3d_df = reorder_df_col(matches_league_3d_df)

    # # Output dataframes
    # matches_league_df.to_pickle(os.path.join(ASSETS_DIR, f'{SERVER}_{LEAGUE}_{LATEST_RELEASE}_matches.pickle'))
    matches_league_df.to_csv(os.path.join(
        ASSETS_DIR, f'{SERVER}_{LEAGUE}_{LATEST_RELEASE}_matches.csv'), index=False)
    matches_league_patch_df.to_pickle(os.path.join(
        ASSETS_DIR, f'{SERVER}_{LEAGUE}_{LATEST_RELEASE}_{PATCH}_matches.pickle'))
    matches_league_patch_df.to_csv(os.path.join(
        ASSETS_DIR, f'{SERVER}_{LEAGUE}_{LATEST_RELEASE}_{PATCH}_matches.csv'), index=False)
    matches_league_3d_df.to_pickle(os.path.join(
        ASSETS_DIR, f'{SERVER}_{LEAGUE}_{LATEST_RELEASE}_{THREEDAY}_matches.pickle'))
    matches_league_3d_df.to_pickle(os.path.join(
        ASSETS_DIR, f'{SERVER}_{LEAGUE}_{LATEST_RELEASE}_latest_matches.pickle'))
    matches_league_3d_df.to_csv(os.path.join(
        ASSETS_DIR, f'{SERVER}_{LEAGUE}_{LATEST_RELEASE}_{THREEDAY}_matches.csv'), index=False)

    # # End
    return [f'# End {SERVER}_{LEAGUE}_{LATEST_RELEASE}_{PATCH}_{THREEDAY} done.']


# Main #
async def main(config: ConfigParser) -> None:
    servers: str = config['servers']
    league: str = config["league"]
    latest_release: str = config['latest_release']
    ranked_id: int = config["ranked_id"]
    patch: str = config["patch"]

    tasks = [asyncio.create_task(start_tft_data_egress(
        server=server, league=league, latest_release=latest_release, ranked_id=ranked_id, patch=patch)) for server in servers]

    done, pending = await asyncio.wait(tasks, timeout=900, return_when=asyncio.ALL_COMPLETED)
    logging.info(f'Done task count: {len(done)}')
    logging.info(f'Pending task count: {len(pending)}')

    for done_task in done:
        if done_task.exception() is None:
            logging.info(''.join(done_task.result()))
        else:
            logging.error("Request got an exception",
                          exc_info=done_task.exception())
    for pending_task in pending:
        pending_task.print_stack()


if __name__ == '__main__':
    args = argparse.ArgumentParser(description='TFT API matches scraper')
    args.add_argument('-c', '--config', default=None, type=str,
                      help='config file path (default: None)')
    # custom cli options to modify configuration from default values given in json file.
    CustomArgs = collections.namedtuple('CustomArgs', 'flags type target')
    options = [
        CustomArgs(['-s', '--servers'], type=str,
                   target='server'),
        CustomArgs(['-l', '--league'], type=str,
                   target='league'),
    ]
    config = ConfigParser.from_args(args, options)

    asyncio.run(main(config))
