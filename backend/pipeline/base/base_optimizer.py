import os
import pickle

import numpy as np
import pandas as pd  # data processing, CSV file I/O (e.g. pd.read_csv)
from abc import abstractmethod

from utils.logger import logging


class BaseOptimizer():
    def __init__(self, model, data_loader, search_method, config):
        self.X_train, self.y_train = data_loader.get_data()
        self.model = model
        self.search_method = search_method
        self.save_dir = config.save_dir
        self.debug = config.debug
        self.config = config

    def _perform_grid_search(self):
        # sorted(sklearn.metrics.SCORERS.keys()) -> get available metrics
        self.search_method.fit(self.X_train, self.y_train)
        return self.search_method

    def _save_model(self, model):
        """Save model to pickle format

        Args:
            model (BaseModel): Model to be saved in binary format
        """
        save_path = os.path.join(self.save_dir, "model.pkl")
        with open(save_path, 'wb') as f:
            pickle.dump(model, f, pickle.HIGHEST_PROTOCOL)

    def load_model(self):
        """Load model from last trained or from config 'model_dir'.
         Keep 'model_dir' empty if you intend to use current model.

        Returns:
            BaseModel: Model to be used for prediction task
        """
        if self.config['model_dir']:
            load_path = os.path.join(self.config['model_dir'], "model.pkl")
        else:
            load_path = os.path.join(self.save_dir, "model.pkl")
        logging.info(f'Loading model from: {load_path}')
        with open(load_path, 'rb') as f:
            model = pickle.load(f)
            logging.info(model)
        return model

    def save_report(self, report, name_txt, prediction_df=None):
        """Save report

        Args:
            report (String): Report content
            name_txt (String): Report filename
            prediction_df (Dataframe, optional): Results to be saved. Defaults to None.
        """
        save_path = os.path.join(self.save_dir, name_txt)
        logging.info(f'Saving report to: {save_path}')
        if isinstance(prediction_df, pd.DataFrame):
            results_path = os.path.join(self.save_dir, 'prediction.csv')
            prediction_df.to_csv(results_path, index=True)
            logging.info(f'Saved prediction to: {results_path}')
        with open(save_path, "w") as text_file:
            text_file.write(report)

    def optimize(self):
        if self.debug:
            self._debug_true()
        else:
            self._debug_false()

    def _debug_false(self):
        gs = self._perform_grid_search()
        model = self.fitted_model(gs)
        train_report = self.create_train_report(gs)
        self._save_model(model)
        self.save_report(train_report, "report_train.txt")

    def _debug_true(self):
        x = self.X_train
        y = self.y_train
        # for each parameter take just the first element from param_grid
        if hasattr(self.search_method, "param_grid"):
            param_grid = self.search_method.param_grid[0].copy()
            for param in param_grid.keys():
                param_grid[param] = param_grid[param][0]

            self.model.set_params(**param_grid)

            logging.debug(
                "-----------------------------------------------------------------")
            logging.debug("Model architecture:")
            logging.debug("input: {}".format(x.shape))
            for layer in self.model:
                if hasattr(layer, "fit_transform"):
                    x = layer.fit_transform(x, y)
                elif hasattr(layer, "fit") and hasattr(layer, "predict"):
                    layer.fit(x, y)
                    x = layer.predict(x)
                else:
                    x = np.array([])
                    logging.debug(f"Warning: {layer} layer dimensions wrong!")

                logging.debug("layer {}: {}".format(layer, x.shape))
            logging.debug(
                "-----------------------------------------------------------------")
        else:
            logging.debug(
                "\n Error: Debug option only available for GridSearch")
        quit()

    def create_train_report(self, cor):
        '''Should return report from training'''
        return "Train report not configured."

    def create_test_report(self, y_test, y_pred):
        '''Should return report from testing'''
        return "Test report not configured."

    @abstractmethod
    def fitted_model(self, cor):
        '''Should return fitted model'''
        raise NotImplementedError
