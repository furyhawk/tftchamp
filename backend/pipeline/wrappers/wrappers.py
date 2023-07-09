# from tensorflow import keras
from typing import Dict, Any
# from scikeras.wrappers import KerasClassifier, KerasRegressor
from sklearn.cross_decomposition import PLSRegression

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'


class PLSRegressionWrapper(PLSRegression):
    def transform(self, X):
        return super().transform(X)

    def fit_transform(self, X, Y):
        return self.fit(X, Y).transform(X)


# class MLPKerasRegressor(KerasRegressor):
#     """ Self contained MLPClassifier
#         By subclassing KerasClassifier,
#         you can embed your Keras model into directly into your estimator class.
#         We start by inheriting from KerasClassifier and defining an
#         __init__ method with all of our parameters.
#     """

#     def __init__(
#         self,
#         hidden_layer_sizes=(50, 25, 10,),
#         optimizer="adam",
#         optimizer__learning_rate=0.001,
#         epochs=70,
#         verbose=0,
#         **kwargs,
#     ):
#         super().__init__(**kwargs)
#         self.hidden_layer_sizes = hidden_layer_sizes
#         self.optimizer = optimizer
#         self.epochs = epochs
#         self.verbose = verbose

#     def _keras_build_fn(self, compile_kwargs: Dict[str, Any]):
#         """ Next, we will embed our model into _keras_build_fn, 
#             which takes the place of get_clf_model.
#             Note that since this is now an part of the model,
#             we no longer need to accept the any parameters in the function signature.
#             We still accept compile_kwargs because we use it to get
#             the optimizer initialized with all of it's parameters.
#         """
#         model = keras.Sequential()
#         inp = keras.layers.Input(shape=(self.n_features_in_))
#         model.add(inp)
#         for hidden_layer_size in self.hidden_layer_sizes:
#             layer = keras.layers.Dense(hidden_layer_size, activation="relu")
#             model.add(layer)
#         # if self.target_type_ == "continuous":
#         #     n_output_units = 1
#         #     # output_activation = "sigmoid"
#         #     loss = "mse"
#         # else:
#         #     raise NotImplementedError(
#         #         f"Unsupported task type: {self.target_type_}")
#         # , activation=output_activation
#         n_output_units = 1
#         loss = "mse"
#         out = keras.layers.Dense(n_output_units)
#         model.add(out)
#         model.compile(loss=loss, optimizer=compile_kwargs["optimizer"])
#         return model


# class MLPKerasClassifier(KerasClassifier):
#     """ Self contained MLPClassifier
#         By subclassing KerasClassifier,
#         you can embed your Keras model into directly into your estimator class.
#         We start by inheriting from KerasClassifier and defining an
#         __init__ method with all of our parameters.
#     """

#     def __init__(
#         self,
#         hidden_layer_sizes=(50, 25, 10,),
#         optimizer="adam",
#         optimizer__learning_rate=0.001,
#         epochs=70,
#         verbose=0,
#         **kwargs,
#     ):
#         super().__init__(**kwargs)
#         self.hidden_layer_sizes = hidden_layer_sizes
#         self.optimizer = optimizer
#         self.epochs = epochs
#         self.verbose = verbose

#     def _keras_build_fn(self, compile_kwargs: Dict[str, Any]):
#         """ Next, we will embed our model into _keras_build_fn, 
#             which takes the place of get_clf_model.
#             Note that since this is now an part of the model,
#             we no longer need to accept the any parameters in the function signature.
#             We still accept compile_kwargs because we use it to get
#             the optimizer initialized with all of it's parameters.
#         """
#         model = keras.Sequential()
#         inp = keras.layers.Input(shape=(self.n_features_in_))
#         model.add(inp)
#         for hidden_layer_size in self.hidden_layer_sizes:
#             layer = keras.layers.Dense(hidden_layer_size, activation="relu")
#             model.add(layer)
#         if self.target_type_ == "binary":
#             n_output_units = 1
#             output_activation = "sigmoid"
#             loss = "binary_crossentropy"
#         elif self.target_type_ == "multiclass":
#             n_output_units = self.n_classes_
#             output_activation = "softmax"
#             loss = "sparse_categorical_crossentropy"
#         else:
#             raise NotImplementedError(
#                 f"Unsupported task type: {self.target_type_}")
#         out = keras.layers.Dense(n_output_units, activation=output_activation)
#         model.add(out)
#         model.compile(loss=loss, optimizer=compile_kwargs["optimizer"])
#         return model
