#!/usr/bin/env python
# coding: utf-8

from wrappers import *

from sklearn.svm import SVC
from sklearn.ensemble import VotingRegressor
from sklearn.tree import ExtraTreeRegressor
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import PolynomialFeatures

from sklearn.linear_model import ElasticNet, Ridge
from sklearn.naive_bayes import GaussianNB
from sklearn.neural_network import MLPRegressor

from xgboost import XGBRegressor

# Soft Voting/Majority Rule classifier for unfitted estimators.
clf1 = ExtraTreeRegressor()
clf2 = XGBRegressor(objective="reg:squarederror",
                    eval_metric="mae", n_estimators=300, max_depth=9)
# clf3 = MLPKerasRegressor()
# clf3 = MLPClassifier(hidden_layer_sizes=(100, 50, 25, 10), max_iter=1000, early_stopping=True)

# ensemble estimator
# eclf = VotingRegressor(
#     estimators=[('etc', clf1), ('xgb', clf2), ('mlp', clf3)])

methods_dict = {
    'ridge': Ridge,
    'pf': PolynomialFeatures,
    'scaler': StandardScaler,
    'preprocessing': NoShowPreprocessing,
    'column_transformer': Column_Wrapper,
    'PLS': PLSRegressionWrapper,
    # 'MLPClass': MLPKerasClassifier,
    # 'MLPReg': MLPKerasRegressor,
    'ELASTICNET': ElasticNet,
    'GNB': GaussianNB,
    'SVC': SVC,
    'PCA': PCA,
    'ETC': ExtraTreeRegressor,
    'MLP': MLPRegressor,
    'XGB': XGBRegressor,
    # 'VCL': eclf,
}
