#!/usr/bin/env python
# coding: utf-8


import os.path

from typing import List
from datetime import date, datetime, timedelta
import argparse
import asyncio
import collections

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pandas import DataFrame, Series
from pandas.plotting import table

from kmodes.kmodes import KModes

from sklearn.cluster import KMeans, MiniBatchKMeans, DBSCAN
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import Normalizer
from sklearn import metrics

# from thefuzz import fuzz

from utils.parse_config import ConfigParser
from tft.api import *
from utils.utils import *
from utils.configuration import settings

pd.options.mode.chained_assignment = None  # default='warn'

RANDOM_STATE = 42
ASSETS_DIR: str = settings.assets_dir
TARGETNAME = settings.targetname  # 'placement'

# # Load TFT asset
tft_assets = read_json(os.path.join(ASSETS_DIR, f'en_us.json'))
# Load TFT set 7
tft7_set = tft_assets['setData'][6]['champions']
# Statics
CHAMPIONS_DICT = {}
for champion in tft7_set:
    # CHAMPIONS_DICT.get(champion["apiName"], [])
    if champion["apiName"] not in CHAMPIONS_DICT:
        CHAMPIONS_DICT[champion["apiName"]] = []
    for trait in champion["traits"]:
        CHAMPIONS_DICT[champion["apiName"]].append(trait)


def impute(df) -> DataFrame:
    for name in df.select_dtypes("number"):
        df[name] = df[name].fillna(0)
    for name in df.select_dtypes("object"):
        df[name] = df[name].fillna("None")
    return df


def get_unit_items_ranking(df: DataFrame, unit: str):
    """Rank top items per champion

    Args:
        df (DataFrame): matches df
        unit (str): champions

    Returns:
        DataFrame: ranked items per champion
    """
    # filter and melt the dataframe
    df = df.filter(
        regex=f'placement|{unit}_item0|{unit}_item1|{unit}_item2')
    df[f'unit'] = f'{unit}'  # fill in current unit
    # join 3 items to 1 column
    df[f'{unit}_items'] = df[[f'{unit}_item0', f'{unit}_item1', f'{unit}_item2']].apply(
        lambda row: ', '.join(row.values.astype(str)), axis=1)
    # sort items for unique combination
    df[f'{unit}_items'] = df[f'{unit}_items'].apply(
        lambda x: ', '.join(sorted(x.split(', '))))
    df = df.filter(regex=f'placement|{unit}_items|unit')
    m = df.melt(
        ['placement', f'unit'], value_name=f'{unit}_items_grp')  # , value_vars=[f'{unit}_items', f'{unit}']
    # group and aggregate mean/median average_placement
    dct = {'value_count': (f'{unit}_items_grp', 'count'),
           'average_placement': ('placement', lambda x: round(x.mean(), 2))}
    return m.groupby([f'unit', f'{unit}_items_grp'], as_index=False).agg(**dct).sort_values(by='average_placement')


def get_augment_ranking(df: DataFrame, augment: str):
    # filter and melt the dataframe
    m = df.filter(regex=r'placement|'+augment).melt(
        'placement', value_name=f'{augment}_grp')
    # group and aggregate mean/median
    dct = {'Value_Count': (f'{augment}_grp', 'count'),
           'average_placement': ('placement', lambda x: round(x.mean(), 2))}
    return m.groupby(f'{augment}_grp', as_index=False).agg(
        **dct).sort_values(by='average_placement')


def add_traits(units_str):

    # for units in units_str.split(', '):
    comp_array = []
    if not units_str:
        return ''
    for unit in units_str.split(', '):
        traits_array = []
        for trait in CHAMPIONS_DICT[unit]:
            # Add first 2 char for trait
            traits_array.append(trait[:2]+trait[-1:])
        traits_str = '-'.join(traits_array) + f'-{unit}'
        comp_array.append(traits_str)

    # print(f'{"".join(comp_array)}')
    return ','.join(comp_array)


def get_unit_comp_ranking(df: DataFrame, units_col, add_trait=True):
    # filter and melt the dataframe
    df = df.filter(['placement']+units_col)
    # join units lvl > 0 to 1 column
    df['comp'] = df[units_col].apply(lambda row: ', '.join(
        row[row > 0].index.values.astype(str)), axis=1)
    if add_trait:
        df['comp'] = df['comp'].apply(add_traits)

    # remove prefix .split('_',1).str[-1]
    df['comp'] = df['comp'].str.replace('TFT7_', '')
    df = df.filter(['placement', 'comp'])
    m = df.melt(
        ['placement'], value_name=f'comp_grp')
    # group and aggregate mean/median average_placement
    dct = {'value_count': (f'comp_grp', 'count'),
           'average_placement': ('placement', lambda x: round(x.mean(), 2))}
    return m.groupby([f'comp_grp'], as_index=False).agg(**dct).sort_values(by='average_placement')


def remove_traits(units_str):
    """Remove units traits from text seperated by comma

    Args:
        units_str (str): traits-unit,traits-unit

    Returns:
        str: Units stripped of traits
    """
    if not units_str:
        return ''

    units_array = []
    for unit in units_str.split(','):
        units_array.append(unit.split('-')[-1])
    units = ', '.join(units_array)
    return units


def get_unit_composition(df: DataFrame, units_col, traits_col):
    # filter and melt the dataframe
    df = df.filter(['placement']+units_col+traits_col)
    return df.sort_values(by='placement')


def get_unit_composition_ranking(df: DataFrame, units_col, add_trait=True):
    # filter and melt the dataframe
    df = df.filter(['placement', 'group']+units_col)
    # join units lvl > 0 to 1 column
    df['comp'] = df[units_col].apply(lambda row: ', '.join(
        row[row > 0].index.values.astype(str)), axis=1)

    if add_trait:
        df['comp'] = df['comp'].apply(add_traits)

    df['comp'] = df['comp'].str.replace('TFT7_', '')
    df = df.filter(['placement', 'group', 'comp'])
    return df.sort_values(by='group')


def save_dataframe(df, filename, colWidths=None, figsize=(10, 10)):
    if not colWidths:
        colWidths = [0.17]*len(df.columns)
    _, ax = plt.subplots(figsize=figsize)  # set size frame

    # ax = plt.subplot(111, frame_on=False)  # no visible frame
    ax.xaxis.set_visible(False)  # hide the x axis
    ax.yaxis.set_visible(False)  # hide the y axis
    ax.set_frame_on(False)  # no visible frame, uncomment if size is ok
    ax.figure.tight_layout()

    dbscan_table = table(ax, df.reset_index(drop=True),
                         loc='best', cellLoc='left')  # , colWidths=colWidths
    dbscan_table.auto_set_font_size(True)  # Activate set fontsize manually
    # dbscan_table.set_fontsize(12) # if ++fontsize is necessary ++colWidths
    dbscan_table.scale(1.2, 1.2)  # change size table
    # Provide integer list of columns to adjust
    dbscan_table.auto_set_column_width(col=list(range(len(df.columns))))
    plt.savefig(os.path.join(
        ASSETS_DIR,
        f'{filename}.png'), transparent=True, dpi=200, bbox_inches='tight')


def cluster_composition_ranking(model, dff, units_col):
    df = dff.copy()
    X = df.copy()
    X.pop(TARGETNAME)
    clusters = model.fit_predict(X)

    df.insert(0, "group", clusters, True)

    df = get_unit_composition_ranking(
        df, units_col, add_trait=False)

    df['grp_count'] = df.groupby(
        ['group'], as_index=False)['group'].transform('count')
    df['grp_placement'] = df.groupby(
        ['group'], as_index=False)['placement'].transform('mean').round(2)
    df['mode'] = df.groupby(
        'group')['comp'].transform(lambda x: pd.Series.mode(x)[0])
    return df


async def start_tft_data_analysis(server: str, league: str, latest_release: str, ranked_id: int, patch: str):
    # Start
    SERVER: str = server
    LEAGUE: str = league
    LATEST_RELEASE: str = latest_release
    RANKED_ID: int = ranked_id    # 1090 normal game 1100 ranked game
    PATCH: date = date.fromisoformat(patch)
    THREEDAY: datetime = (
        datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    # # Data Loading

    prefix: str = f'{SERVER}_{LEAGUE}_{LATEST_RELEASE}_{PATCH}'
    logging.info(
        f'# Starting {prefix} loading.')

    # raw_df: DataFrame = pd.read_pickle(os.path.join(ASSETS_DIR, f'{SERVER}_{LEAGUE}_{LATEST_RELEASE}_{PATCH}_matches.pickle'))
    raw_df: DataFrame = pd.read_pickle(os.path.join(
        ASSETS_DIR, f'{prefix}_matches.pickle'))

    # # Preprocessing
    raw_df: DataFrame = impute(raw_df)
    logging.info(
        f'Loaded DataFrame shape: {raw_df.shape}')

    X: DataFrame = raw_df.drop(['match_id'], axis=1)
    y: Series = X.pop(TARGETNAME)
    X.fillna('', inplace=True)

    numeric_cols: List = X.select_dtypes(include=np.number).columns.tolist()
    categorical_cols = X.select_dtypes(
        include=['object', 'category']).columns.tolist()

    # traits level columns
    traits_col: list = [s for s in numeric_cols if "Set7" in s]
    # units level columns
    units_col: list = [s for s in numeric_cols if "TFT7" in s]
    # augments columns
    augments_col: list[str] = ['augment0', 'augment1', 'augment2']
    # units items columns
    items_col = [s for s in categorical_cols if s not in augments_col]

    X[f'items_count'] = X[items_col].apply(
        lambda row: sum(x != 'None' for x in row), axis=1)
    X[f'traits_sum'] = X[traits_col].sum(axis=1)
    X[f'units_sum'] = X[units_col].sum(axis=1)

    numeric_cols = X.select_dtypes(include=np.number).columns.tolist()
    categorical_cols = X.select_dtypes(
        include=['object', 'category']).columns.tolist()

    X[numeric_cols] = X[numeric_cols].applymap(np.int64)

    # Matches DataFrame #
    matches_df = X.copy()
    matches_df[TARGETNAME] = y

    # # Augments Ranking

    # ## Stage 2-1 augment ranking
    augment0_rank_df = get_augment_ranking(matches_df, 'augment0')
    save_dataframe(
        augment0_rank_df, f'{prefix}_augment0_ranking')
    # Output
    augment0_rank_df.to_csv(os.path.join(
        ASSETS_DIR, f'{prefix}_augment0_ranking.csv'), index=False)

    # ## Stage 3-2 augment ranking
    augment1_rank_df = get_augment_ranking(matches_df, 'augment1')
    save_dataframe(
        augment1_rank_df, f'{prefix}_augment1_ranking')
    # Output
    augment1_rank_df.to_csv(os.path.join(
        ASSETS_DIR, f'{prefix}_augment1_ranking.csv'), index=False)

    # ## Stage 4-2 augment ranking
    augment2_rank_df = get_augment_ranking(matches_df, 'augment2')
    save_dataframe(
        augment2_rank_df, f'{prefix}_augment2_ranking')
    # Output
    augment2_rank_df.to_csv(os.path.join(
        ASSETS_DIR, f'{prefix}_augment2_ranking.csv'), index=False)

    # # Items Ranking

    # Get top5 value_count >= 12
    top5_items_list = []
    for unit in units_col:
        df = get_unit_items_ranking(df=matches_df, unit=unit)
        df = df[df['value_count'] >= 12][:5]  # Top 5 with counts >= 12
        top5_items_list.extend(df.values)

    top5_items_list = pd.DataFrame(top5_items_list, columns=[
        'unit', 'items', 'value_count',	'average_placement'])
    save_dataframe(
        top5_items_list, f'{prefix}_top5_items')
    # Output
    top5_items_list.to_csv(os.path.join(
        ASSETS_DIR, f'{prefix}_top5_items.csv'), index=False)

    # ## Top 1 items
    # top5_items_list.groupby('unit').head(1)

    # # Team Composition Ranking

    # Get top5
    # comp_df = get_unit_comp_ranking(matches_df, units_col)

    # top5_comp_list = []
    # m = comp_df[comp_df['value_count'] >= 1]  # [:5] #Top 5 with counts >= 12
    # top5_comp_list.extend(m.values)
    # comp_ranking_df = pd.DataFrame(top5_comp_list, columns=[
    #     'comp', 'value_count', 'average_placement'])

    # comp_ranking_df  # .groupby('comp').head(1)

    # composition_ranking_df = comp_ranking_df.copy()

    # # Team composition Clustering
    units_comp_df: DataFrame = get_unit_composition(
        matches_df, units_col, traits_col)

    # ## KMode
    # using integers

    # Building the model with 3 clusters
    kmode = KModes(n_clusters=30, init="random", n_init=5, verbose=0)

    # top5_comp_ranking_list = []
    # # [:5] #Top 5 with counts >= 12
    # m = kmode_ranking_df[kmode_ranking_df['grp_count'] >= 10]
    # top5_comp_ranking_list.extend(m.values)
    # top_kmode_ranking_df = pd.DataFrame(top5_comp_ranking_list, columns=[
    #                                     'placement', 'group', 'comp', 'grp_count', 'grp_placement'])

    kmode_ranking_df = cluster_composition_ranking(
        kmode, units_comp_df, units_col)
    kmode_df = kmode_ranking_df.groupby(['group']).head(
        1).sort_values(by='grp_placement')
    save_dataframe(
        kmode_df, f'{prefix}_kmode_comp_ranking')
    # Output
    kmode_ranking_df.to_csv(os.path.join(
        ASSETS_DIR, f'{prefix}_kmode_comp_ranking.csv'), index=False)

    # ## KMeans
    # normalization to improve the k-means result.
    normalizer = Normalizer(copy=False)
    # Building the model with 30 clusters
    kms = KMeans(n_clusters=30, init="k-means++", n_init=10, verbose=0)
    kmeans = make_pipeline(normalizer, kms)

    kmeans_ranking_df = cluster_composition_ranking(
        kmeans, units_comp_df, units_col)
    kmeans_df = kmeans_ranking_df.groupby(['group']).head(
        1).sort_values(by='grp_placement')

    save_dataframe(
        kmeans_df, f'{prefix}_kmeans_comp_ranking')
    # Output
    kmeans_ranking_df.to_csv(os.path.join(
        ASSETS_DIR, f'{prefix}_kmeans_comp_ranking.csv'), index=False)

    # ## DBSCAN
    # Building the model with X clusters
    # normalization to improve the k-means result.
    normalizer = Normalizer(copy=False)
    dbs = DBSCAN(eps=0.37, metric='euclidean', min_samples=3,
                 n_jobs=-1)  # eps=0.053, metric='cosine'
    dbscan = make_pipeline(normalizer, dbs)
    dbscan_ranking_df = cluster_composition_ranking(
        dbscan, units_comp_df, units_col)

    dbscan_df = dbscan_ranking_df.groupby(['group']).head(
        1).sort_values(by='grp_placement', ascending=True)[:36]
    save_dataframe(
        dbscan_df, f'{prefix}_dbscan_comp_ranking')

    # Output
    dbscan_ranking_df.to_csv(os.path.join(
        ASSETS_DIR, f'{prefix}_dbscan_comp_ranking.csv'), index=False)
    # # End
    return [f'# End {prefix} done.']

# Main #


async def main(config: ConfigParser) -> None:
    servers: str = config['servers']
    league: str = config["league"]
    latest_release: str = config['latest_release']
    ranked_id: int = config["ranked_id"]
    patch: str = config["patch"]

    tasks = [asyncio.create_task(start_tft_data_analysis(
        server=server, league=league, latest_release=latest_release, ranked_id=ranked_id, patch=patch)) for server in servers]

    done, pending = await asyncio.wait(tasks, timeout=1800, return_when=asyncio.ALL_COMPLETED)
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
