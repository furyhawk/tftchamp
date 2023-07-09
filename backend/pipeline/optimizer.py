import argparse
import collections

from utils.parse_config import ConfigParser
from utils.parse_params import modify_params, get_lib
import data_loaders.data_loaders as data_loaders_
import models.models as models_
import optimizers.optimizers as optimizers_

import sklearn.model_selection as model_selection_
import pandas as pd  # data processing, CSV file I/O (e.g. pd.read_csv)
from pymongo import MongoClient

from utils.configuration import settings


def load_data_optimizer(config):
    prefix: str = f'{config["server"]}_{config["league"]}_{config["latest_release"]}_{config["patch"]}'
    # Create Mongodb client using env uri
    client = MongoClient(settings.db_uri, connect=False)
    db = client[settings.db_name]
    # Get all unique matches_id from assets dir
    binary_collection = db[f'{prefix}_binary']
    model_collection = db[f'{prefix}_model']

    # 1. Create data_loader module
    # Load X, y
    data_loader = config.init_obj(
        'data_loader', data_loaders_, **{'training': True, 'label_name': config['label_name']})
    # 2. Create estimator model and the scoring metrics
    model = config.init_obj('model', models_).created_model()
    cross_val = config.init_obj('cross_validation', model_selection_)
    minmax, scoring = config['score'].split()

    # 3. Create search method
    search_method_params = {
        'estimator': model,
        'scoring': scoring,
        'cv': cross_val
    }
    search_method_params, search_type = modify_params(
        search_method_params, config)
    search_method = config.init_obj(
        'search_method', get_lib(search_type), **search_method_params)

    # 4. Create Optimizer module
    Optimizer = config.import_module('optimizer', optimizers_)
    optim = Optimizer(model=model,
                      data_loader=data_loader,
                      search_method=search_method,
                      scoring=scoring,
                      minmax=minmax,
                      config=config,
                      binary_collection=binary_collection,
                      model_collection=model_collection
                      )

    return optim


def main(config):
    """Main App

    Args:
        config (Config): Class object for configurations
    """
    

    # 1. Load data and optimizer function
    optim = load_data_optimizer(config)

    # 2. Optimize and train model if True
    if config['train_model']:
        optim.optimize()
    else:
        assert (config['model_dir'] != '') & (config['test_model']
                                              ), 'Without training, maintain config.model_dir with the path to load model.pkl.'

    # 3. Model prediction(testing set) output
    if config['test_model']:
        data_loader = config.init_obj(
            'data_loader', data_loaders_, **{'training': False, 'label_name': config['label_name']})
        X_test, y_test = data_loader.get_data()
        model = optim.load_model()
        y_pred = model.predict(X_test)

        # X is DataFrame, output X as csv
        if isinstance(X_test, pd.DataFrame):
            prediction_df = X_test.copy()
            prediction_df[config['label_name']] = y_pred
            test_report = optim.create_test_report(y_test, y_pred)
            optim.save_report(test_report, 'report_test.txt', prediction_df) #binary_collection
        else:
            test_report = optim.create_test_report(y_test, y_pred)#binary_collection
            optim.save_report(test_report, 'report_test.txt')


if __name__ == '__main__':

    args = argparse.ArgumentParser(description='TFTChamp pipeline')
    args.add_argument('-c', '--config', default=None, type=str,
                      help='config file path (default: None)')

    # custom cli options to modify configuration from default values given in json file.
    CustomArgs = collections.namedtuple('CustomArgs', 'flags type target')
    options = [
        CustomArgs(['-cv', '--cross_validation'], type=int,
                   target='cross_validation;args;n_repeats'),
    ]

    config = ConfigParser.from_args(args, options)
    main(config)
