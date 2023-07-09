#!/usr/bin/env python
# coding: utf-8

import argparse
import asyncio
import collections
from datetime import date, datetime, timedelta

from pymongo import MongoClient, DESCENDING

# from tft.api import *
from utils.parse_config import ConfigParser
from utils.logger import logging
from utils.utils import *
from utils.configuration import settings
import os.path

import pandas as pd
import numpy as np


# # Config
TARGETNAME: str = settings.targetname  # 'placement'


def handle_nas(df, default_date='2020-01-01'):
    """
    :param df: a dataframe
    :param d: current iterations run_date
    :return: a data frame with replacement of na values as either 0 for numeric fields, 'None' for text and False for bool
    """
    numeric_cols: list = df.select_dtypes(include=np.number).columns.tolist()
    categorical_cols: list = df.select_dtypes(
        include=['object', 'category']).columns.tolist()

    for f in df.columns:

        # integer
        if f in numeric_cols:
            df[f] = df[f].fillna(0)

        # dates
        elif df[f].dtype == '<M8[ns]':
            df[f] = df[f].fillna(pd.to_datetime(default_date))

        # boolean
        elif df[f].dtype == 'bool':
            df[f] = df[f].fillna(False)

        # string
        elif f in categorical_cols:
            df[f] = df[f].fillna('None')

    return df


async def process_matches(df) -> list[dict]:
    matches_array: list = []

    for match_row in df:

        match_id: str = match_row['metadata']['match_id']

        for participant in match_row['info']['participants']:
            match: dict = {}
            # db unique id
            match['_id'] = match_id + '-' + participant['puuid']
            match['match_id'] = match_id
            # match['level'] = participant['level']
            match['placement'] = participant['placement']
            # match['players_eliminated'] = participant['players_eliminated']
            # match['total_damage_to_players'] = participant['total_damage_to_players']

            for augment_index, augment in enumerate(participant['augments']):
                match[f'augment{augment_index}'] = augment

            for _, trait in enumerate(participant['traits']):
                match[f'{trait["name"]}'] = (
                    trait["tier_current"] / trait["tier_total"]) * 12

            for _, unit in enumerate(participant['units']):
                tier: int = unit["tier"]
                rarity: int = unit["rarity"]
                # if match[f'{unit["character_id"]}']: # Double or more units
                #     match[f'{unit["character_id"]}'] += tier * rarity
                # else:
                match[f'{unit["character_id"]}'] = tier * rarity
                # match['TFT7b_Heimerdinger_item0'] = 'None'
                # match['TFT7b_Heimerdinger_item1'] = 'None'
                # match['TFT7b_Heimerdinger_item2'] = 'None'
                # match['TFT7b_Lulu_item0'] = 'None'
                # match['TFT7b_Lulu_item1'] = 'None'
                # match['TFT7b_Lulu_item2'] = 'None'
                # match['TFT7b_Tristana_item0'] = 'None'
                # match['TFT7b_Tristana_item1'] = 'None'
                # match['TFT7b_Tristana_item2'] = 'None'
                for item_index, item in enumerate(unit['itemNames']):
                    match[f'{unit["character_id"]}_item{item_index}'] = item.split(
                        '_')[-1]

            matches_array.append(match)

    return matches_array


def reorder_df_col(df):
    """ reorder dataframe columns"""
    fixed_cols = ['placement', 'match_id',
                  'augment0', 'augment1', 'augment2']
    all_cols = df.columns
    to_sort_cols = list(set(all_cols) - set(fixed_cols))

    return df.reindex(columns=fixed_cols + sorted(to_sort_cols))


async def start_tft_data_egress(server: str, league: str, latest_release: str, ranked_id: int, patch: str, save_csv: bool):
    # config to process
    SERVER: str = server
    LEAGUE: str = league
    LATEST_RELEASE: str = latest_release
    RANKED_ID: int = ranked_id    # 1090 normal game 1100 ranked game 1130 turbo
    PATCH: date = date.fromisoformat(patch)
    THREEDAY: datetime = (
        datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")

    # Create Mongodb client using env uri
    client = MongoClient(settings.db_uri)
    db = client[settings.db_name]

    logging.info(
        f'# Starting {SERVER}_{LEAGUE}_{LATEST_RELEASE}_{PATCH} loading.')

    summoners_collection = db[f'{SERVER}_{LEAGUE}_summoners']
    summoners_df = pd.DataFrame(list(summoners_collection.find()))
    # # Load unique matches id
    # Get all unique matches_id from assets dir {'game_version': {'$regex': LATEST_RELEASE}}
    matches_detail_collection = db[SERVER + '_' + 'matches_detail']
    matches_asset: list = load_league_matches_db(
        collection=matches_detail_collection, summoners_df=summoners_df)
    logging.info(
        f'Loaded {SERVER}_{LEAGUE}_{LATEST_RELEASE}_{PATCH}: {len(matches_asset)}.')

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

    del matches_asset
    logging.info(f'uniq_matches: {len(uniq_matches)}')

    # ## Filter by LATEST_RELEASE version and RANKED_ID game.
    latest_matches = [match for match in uniq_matches if (LATEST_RELEASE in match['info']['game_version']) and (
        RANKED_ID == match['info']['queue_id'])]
    # Since last patch matches
    latest_patch_matches = [match for match in uniq_matches if (LATEST_RELEASE in match['info']['game_version'])
                            and (PATCH <= date.fromtimestamp(match['info']['game_datetime']/1000.0))]
    # Last 3 days matches
    latest_3d_matches = [match for match in uniq_matches if (LATEST_RELEASE in match['info']['game_version'])
                         and ((datetime.now() - timedelta(days=3)) <= datetime.fromtimestamp(match['info']['game_datetime']/1000.0))
                         and (PATCH <= date.fromtimestamp(match['info']['game_datetime']/1000.0))]

    del uniq_matches
    logging.info(f'latest_matches: {len(latest_matches)}')
    logging.info(f'latest_patch_matches: {len(latest_patch_matches)}')
    logging.info(f'latest_3d_matches: {len(latest_3d_matches)}')

    # # Process api details to datasets rows
    matches_array = await process_matches(latest_matches)
    matches_patch_array = await process_matches(latest_patch_matches)
    matches_3d_array = await process_matches(latest_3d_matches)

    # Normalize dict to dataframe
    matches_league_df = pd.json_normalize(matches_array)
    matches_league_patch_df = pd.json_normalize(matches_patch_array)
    matches_league_3d_df = pd.json_normalize(matches_3d_array)

    # ## Sort and reorder columns
    matches_league_df = reorder_df_col(matches_league_df)
    matches_league_patch_df = reorder_df_col(matches_league_patch_df)
    matches_league_3d_df = reorder_df_col(matches_league_3d_df)

    # Cleanup NaN
    matches_league_df = handle_nas(matches_league_df)
    matches_league_patch_df = handle_nas(matches_league_patch_df)
    matches_league_3d_df = handle_nas(matches_league_3d_df)

    # # Output dataframes
    matches_collection = db[f'{SERVER}_{LEAGUE}_{LATEST_RELEASE}_matches']
    # matches_collection.create_index([("match_id", DESCENDING)])
    write_collection_db(
        matches_league_df.to_dict('records'), collection=matches_collection, update=False)
    write_collection_db(
        matches_league_patch_df.to_dict('records'), collection=db[f'{SERVER}_{LEAGUE}_{LATEST_RELEASE}_{PATCH}_matches'], update=False)
    write_collection_db(
        matches_league_3d_df.to_dict('records'), collection=db[f'{SERVER}_{LEAGUE}_{LATEST_RELEASE}_3days_matches'], update=False)

    if save_csv:
        matches_league_patch_df.to_csv(os.path.join(
            ASSETS_DIR, f'{SERVER}_{LEAGUE}_{LATEST_RELEASE}_{PATCH}_matches.csv'), index=False)
        matches_league_3d_df.to_csv(os.path.join(
            ASSETS_DIR, f'{SERVER}_{LEAGUE}_{LATEST_RELEASE}_3days_matches.csv'), index=False)
    # matches_league_patch_df.iloc[[0]].to_json(os.path.join(
    #     ASSETS_DIR, f'{SERVER}_{LEAGUE}_{LATEST_RELEASE}_{PATCH}_matches.json'))

    client.close()
    # # End
    return [f'# End {SERVER}_{LEAGUE}_{LATEST_RELEASE}_{PATCH}_{THREEDAY} done.']


# Main #
async def main(config: ConfigParser) -> None:
    servers: str = config['servers']
    league: str = config["league"]
    latest_release: str = config['latest_release']
    ranked_id: int = config["ranked_id"]
    patch: str = config["patch"]
    save_csv: bool = config["save_csv"]

    tasks = [asyncio.create_task(start_tft_data_egress(
        server=server, league=league, latest_release=latest_release, ranked_id=ranked_id, patch=patch, save_csv=save_csv)) for server in servers]

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
        CustomArgs(['-v', '--save_csv'], type=bool,
                   target='save_csv'),
    ]
    config = ConfigParser.from_args(args, options)

    asyncio.run(main(config))
