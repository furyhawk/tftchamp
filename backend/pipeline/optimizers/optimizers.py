import io
import os
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from bson.binary import Binary
from base import BaseOptimizer
from sklearn.metrics import classification_report, mean_absolute_error

from utils.logger import logging


def plot_prediction(y_true, y_predict, save_dir, model):
    area = (30 * np.random.rand(len(y_predict))) ** 2
    # Plot y_true vs. y_pred
    plt.figure(figsize=(10, 10))
    plt.scatter(y_true, y_predict, s=area, color="r", alpha=0.07)
    plt.plot(
        [plt.xlim()[0], plt.xlim()[1]], [plt.xlim()[0], plt.xlim()[1]], "--", color="k"
    )
    plt.gca().set_aspect("equal")
    plt.xlabel("y_true")
    plt.ylabel("y_pred")
    plt.title("Actual vs Predicted")
    plt.savefig(
        os.path.join(save_dir, f"{type(model[-1]).__name__}_ActualvsPredicted.png"),
        dpi=300,
    )


class OptimizerClassification(BaseOptimizer):
    """Define Optimizer for Classification dataset

    Args:
        BaseOptimizer (BaseOptimizer): Base class
    """

    def __init__(
        self,
        model,
        data_loader,
        search_method,
        scoring,
        minmax,
        config,
        binary_collection=None,
        model_collection=None,
    ):
        self.scoring = scoring
        self.minmax = minmax
        self.binary_collection = binary_collection
        self.model_collection = model_collection
        super().__init__(model, data_loader, search_method, config)

    def fitted_model(self, cor):
        clf_results = cor.cv_results_
        params = np.array(clf_results["params"])
        means = clf_results["mean_test_score"]

        if self.minmax == "min":
            sort_idx = np.argsort(means)
        if self.minmax == "max":
            sort_idx = np.argsort(means)[::-1]

        params_sorted = params[sort_idx]
        self.model.set_params(**params_sorted[0])  # define the best model
        self.model.fit(self.X_train, self.y_train)

        return self.model

    def create_train_report(self, cor):
        """Create report

        Args:
            cor (_type_): fit results

        Returns:
            string: report
        """
        logging.info(f"Optimizing for: {self.scoring}")
        logging.info("_________________")

        clf_results = cor.cv_results_
        params = np.array(clf_results["params"])
        means = clf_results["mean_test_score"]
        stds = clf_results["std_test_score"]
        fit_time = sum(clf_results["mean_fit_time"])

        if self.minmax == "min":
            sort_idx = np.argsort(means)
        if self.minmax == "max":
            sort_idx = np.argsort(means)[::-1]

        indexes = np.arange(len(means))

        indexes_sorted = indexes[sort_idx]
        means_sorted = means[sort_idx]
        stds_sorted = stds[sort_idx]
        params_sorted = params[sort_idx]

        train_report = f"###   Optimizing for {self.scoring}   ###\n\n"
        for idx, mean, std, params_ in zip(
            indexes_sorted, means_sorted, stds_sorted, params_sorted
        ):
            logging.info(
                "%d   %0.3f (+/-%0.03f) for %r" % (idx, mean, std * 2, params_)
            )
            train_report += f"{mean:.3f}  +/-{std*2:.3f}  for  {params_}\n"
        train_report += f"\n###   Best model:   ###\n\n {str(self.model)}"
        train_report += f"\n Number of samples used for training: {len(self.y_train)}"
        train_report += f"\n fit_time used for training: {fit_time:.1f}"
        logging.info("\n Report on train data:\n")
        logging.info(train_report)

        return train_report

    def create_test_report(self, y_test, y_pred):
        """create classification test report using sklearn.metrics.classification_report
        https://scikit-learn.org/stable/modules/generated/sklearn.metrics.classification_report.html?highlight=classification_report
        """
        test_report = str(classification_report(y_test, y_pred))
        test_report += f"\n\n True Values:\n {y_test}"
        test_report += f"\n Pred Values:\n {y_pred}"
        logging.info("\n Report on test data:\n")
        logging.info(f"\n {test_report}")

        return test_report


class OptimizerRegression(BaseOptimizer):
    def __init__(
        self,
        model,
        data_loader,
        search_method,
        scoring,
        minmax,
        config,
        binary_collection=None,
        model_collection=None,
    ):
        self.scoring = scoring
        self.minmax = minmax
        self.binary_collection = binary_collection
        self.model_collection = model_collection
        super().__init__(model, data_loader, search_method, config)

    def fitted_model(self, cor):
        clf_results = cor.cv_results_
        params = np.array(clf_results["params"])
        means = clf_results["mean_test_score"]

        if self.minmax == "min":
            sort_idx = np.argsort(means)
        if self.minmax == "max":
            sort_idx = np.argsort(means)[::-1]

        params_sorted = params[sort_idx]
        self.model.set_params(**params_sorted[0])  # define the best model
        self.model.fit(self.X_train, self.y_train)

        return self.model

    def _save_model(self, model):
        """Save model to pickle format

        Args:
            model (BaseModel): Model to be saved in binary format
        """
        prefix: str = f'{self.config["server"]}_{self.config["league"]}_{self.config["latest_release"]}_{self.config["patch"]}'
        # Save to db binary collection
        if self.model_collection is not None:
            buf = io.BytesIO()
            pickle.dump(model, buf, pickle.HIGHEST_PROTOCOL)

            # serialization
            self.model_collection.update_one(
                {
                    "_id": f"{prefix}_model",
                },
                {
                    "$set": {
                        "model": Binary(buf.getbuffer().tobytes()),
                        "text": f"{type(self.model[-1]).__name__}",
                    }
                },
                upsert=True,
            )
            buf.close()

        super()._save_model(model)

    def create_train_report(self, cor):
        """Create report

        Args:
            cor (_type_): fit results

        Returns:
            string: report
        """
        logging.info(f"Optimizing for: {self.scoring}")
        logging.info("_________________")

        prefix: str = f'{self.config["server"]}_{self.config["league"]}_{self.config["latest_release"]}_{self.config["patch"]}'

        clf_results = cor.cv_results_
        params = np.array(clf_results["params"])
        means = clf_results["mean_test_score"]
        stds = clf_results["std_test_score"]
        fit_time = sum(clf_results["mean_fit_time"])

        if self.minmax == "min":
            sort_idx = np.argsort(means)
        if self.minmax == "max":
            sort_idx = np.argsort(means)[::-1]

        indexes = np.arange(len(means))

        indexes_sorted = indexes[sort_idx]
        means_sorted = means[sort_idx]
        stds_sorted = stds[sort_idx]
        params_sorted = params[sort_idx]

        train_report = f"###   Optimizing for {self.scoring}   ###\n\n"
        for idx, mean, std, params_ in zip(
            indexes_sorted, means_sorted, stds_sorted, params_sorted
        ):
            logging.info(
                "%d   %0.3f (+/-%0.03f) for %r" % (idx, mean, std * 2, params_)
            )
            train_report += f"{mean:.3f}  +/-{std*2:.3f}  for  {params_}\n"
        train_report += f"\n###   Best model:   ###\n\n {str(self.model)}"

        # If estimator has feature_importances_ attribute for Feature Importances rcParams['figure.figsize'] = 40, 12
        # TODO column_transformer abstraction
        if hasattr(self.model[-1], "feature_importances_"):
            feature_names = self.model["column_transformer"].get_feature_names_out()
            feature_importances = pd.Series(
                self.model[-1].feature_importances_, index=feature_names
            ).sort_values(ascending=True)
            plt.figure(figsize=(13, 18))
            ax = feature_importances[-50:].plot.barh()  # Top 50
            ax.set_title(
                f"{str(type(self.model[-1]).__name__)} {prefix} Feature Importances"
            )
            # ax.figure.figsize = [13, 25]
            ax.set_xlabel("correlation(abs) against placement")
            ax.set_ylabel("features")
            ax.figure.tight_layout()
            ax.figure.savefig(
                os.path.join(
                    self.save_dir,
                    f"{type(self.model[-1]).__name__}_feature_importances.png",
                ),
                dpi=400,
            )
            train_report += f"\nget_feature_names_out:\n\n {str(self.model['column_transformer'].get_feature_names_out())}"
            train_report += f"\nfeature_importances_:\n\n {str(self.model[-1].feature_importances_)}"
            feature_importances.to_csv(
                os.path.join(
                    self.save_dir,
                    f"{type(self.model[-1]).__name__}_feature_importances.csv",
                ),
                index=False,
            )

            # Save to db binary collection
            if self.binary_collection is not None:
                buf = io.BytesIO()
                ax.figure.savefig(
                    buf, format="png", transparent=True, bbox_inches="tight"
                )

                # serialization
                self.binary_collection.update_one(
                    {
                        "_id": f"{prefix}_feature_importances",
                    },
                    {
                        "$set": {
                            "image": Binary(buf.getbuffer().tobytes()),
                            "text": """Feature Importance refers to techniques that calculate a score
                                        for all the input features for a given model —
                                        the scores simply represent the “importance” of each feature.
                                        A higher score means that the specific feature will have a larger
                                        effect on the model that is being used to predict a certain variable.""",
                        }
                    },
                    upsert=True,
                )
                buf.close()

        train_report += f"\nNumber of samples used for training: {len(self.y_train)}"
        train_report += f"\nfit_time used for training: {fit_time:.1f}"
        logging.info("\n\n### Report on train data:\n")
        logging.info(train_report)

        return train_report

    def create_test_report(self, y_test, y_pred):
        plot_prediction(y_test, y_pred, self.save_dir, self.model)
        mae = mean_absolute_error(y_test, y_pred)
        mae_rounded = mean_absolute_error(y_test, np.rint(y_pred))
        test_report = f"\n\nNumber of samples used for testing: {len(y_test)}"
        test_report += f"\nTrue Values:\n {y_test}"
        test_report += f"\nPred Values:\n {y_pred}"
        test_report += f"\nMAE: {mae} \nRounded MAE: {mae_rounded}"
        logging.info("\n\n### Report on test data:\n")
        logging.info(test_report)

        return test_report
