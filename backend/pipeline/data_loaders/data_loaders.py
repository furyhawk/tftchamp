from base import BaseDataLoader
from data_loaders import data_handler
from typing import List

from pymongo import MongoClient

from sklearn.datasets import load_iris, make_classification
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import make_pipeline

import numpy as np
import pandas as pd  # data processing

from utils.utils import *
from utils.logger import logging

ASSETS_DIR = settings.assets_dir
SERVER = 'na1'  # euw1 na1 kr oc1
LEAGUE = 'challengers'
LATEST_RELEASE = '12.12.450.4196'  # '12.12.450.4196'


def impute(df):
    for name in df.select_dtypes("number"):
        df[name] = df[name].fillna(0)
    for name in df.select_dtypes("object"):
        df[name] = df[name].fillna("None")
    return df


class TFT_Challengers(BaseDataLoader):
    def __init__(self, data_path, shuffle, test_split, random_state, stratify, training, label_name):
        '''set data_path in configs if data localy stored'''
        # Create Mongodb client using env uri
        client = MongoClient(settings.db_uri)
        db = client[settings.db_name]

        # # Load unique matches id
        # Get all unique matches_id from assets dir
        raw_collection = db[f'{data_path}']
        raw_df = pd.DataFrame(list(raw_collection.find()))

        # Clean up dataset
        raw_df = impute(raw_df)
        X = raw_df.drop(['match_id','_id'], axis=1)
        y = X.pop(label_name)
        X.fillna('', inplace=True)
        numeric_cols = X.select_dtypes(include=np.number).columns.tolist()
        categorical_cols = X.select_dtypes(
            include=['object', 'category']).columns.tolist()
        X[numeric_cols] = X[numeric_cols].applymap(np.int64)

        # traits level columns
        traits_col: list = [s for s in numeric_cols if "Set7" in s]
        # units level columns
        units_col: list = [s for s in numeric_cols if "TFT7" in s]
        # augments columns
        augments_col: list[str] = ['augment0', 'augment1', 'augment2']
        # units items columns
        items_col = [s for s in categorical_cols if s not in augments_col]

        # Feature engineering
        X[f'items_count'] = X[items_col].apply(
            lambda row: sum(x != 'None' for x in row), axis=1)
        X[f'traits_sum'] = X[traits_col].sum(axis=1)
        X[f'units_sum'] = X[units_col].sum(axis=1)

        # one_hot_encoder = OneHotEncoder(handle_unknown="ignore", sparse=False)
        # preproc = StandardScaler()
        # # Encode category columns.
        # logistic_regression_pipeline = ColumnTransformer(
        #     transformers=[
        #         ("one_hot_time", one_hot_encoder, categorical_cols),
        #     ],
        #     remainder=preproc,
        #     verbose_feature_names_out=False,
        # )
        # X = logistic_regression_pipeline.fit_transform(X)
        X_train, X_test, y_train, y_test = train_test_split(X, y,
                                                            test_size=test_split,
                                                            random_state=1,
                                                            shuffle=shuffle)

        data_handler.X_data = X_train
        data_handler.y_data = y_train
        data_handler.X_data_test = X_test
        data_handler.y_data_test = y_test

        super().__init__(data_handler, shuffle, test_split, random_state, stratify, training)


class TestClassification(BaseDataLoader):
    """Test case for classification pipeline
    """

    def __init__(self, data_path, shuffle, test_split, random_state, stratify, training, label_name):
        '''set data_path in configs if data localy stored'''

        X, y = load_iris(return_X_y=True)
        data_handler.X_data = X
        data_handler.y_data = y

        super().__init__(data_handler, shuffle, test_split, random_state, stratify, training)


class TestKerasClassification(BaseDataLoader):
    """Test case for keras classification pipeline
    """

    def __init__(self, data_path, shuffle, test_split, random_state, stratify, training, label_name):
        '''set data_path in configs if data localy stored'''

        X, y = make_classification(1000, 20, n_informative=10, random_state=0)
        data_handler.X_data = X.astype(np.float32)
        data_handler.y_data = y.astype(np.int64)

        super().__init__(data_handler, shuffle, test_split, random_state, stratify, training)


class Regression(BaseDataLoader):
    def __init__(self, data_path, shuffle, test_split, random_state, stratify, training, label_name):
        '''set data_path in configs if data localy stored'''
        data_url = "http://lib.stat.cmu.edu/datasets/boston"
        raw_df = pd.read_csv(data_url, sep="\s+", skiprows=22, header=None)
        data = np.hstack([raw_df.values[::2, :], raw_df.values[1::2, :2]])
        target = raw_df.values[1::2, 2]
        # X, y = load_boston(return_X_y=True)
        X_train, X_test, y_train, y_test = train_test_split(data, target,
                                                            test_size=0.2,
                                                            random_state=1,
                                                            shuffle=True)

        data_handler.X_data = X_train
        data_handler.y_data = y_train
        data_handler.X_data_test = X_test
        data_handler.y_data_test = y_test

        super().__init__(data_handler, shuffle, test_split, random_state, stratify, training)
