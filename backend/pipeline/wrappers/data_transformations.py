from collections import defaultdict
from sklearn.preprocessing import LabelEncoder, StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.utils.validation import check_X_y, check_array, check_is_fitted
from sklearn.base import BaseEstimator, TransformerMixin

import pandas as pd  # data processing, CSV file I/O (e.g. pd.read_csv)
pd.options.mode.chained_assignment = None  # default='warn'

# from utils.utils import trace

class Column_Wrapper(BaseEstimator, TransformerMixin):
    """ Column transformer for TFT dataset.
        OneHotEncoder for the rest of categorical values.
    """

    def __init__(self):
        self.column_transformer = None

    def fit(self, X, y=None):
        categorical_cols = X.select_dtypes(
            include=['object', 'category']).columns.tolist()
        one_hot_encoder = OneHotEncoder(
            handle_unknown="ignore", sparse=False)

        preproc = StandardScaler()

        self.column_transformer = ColumnTransformer(
            transformers=[
                ("one_hot_time", one_hot_encoder, categorical_cols),
            ],
            remainder=preproc,
            verbose_feature_names_out=False,
        )
        self.column_transformer.fit(X)
        self.is_fitted_ = True
        return self

    def transform(self, X):
        check_is_fitted(self)
        assert self.column_transformer != None
        X = self.column_transformer.transform(X)
        return X
    # @trace
    def get_feature_names_out(self):
        check_is_fitted(self)
        assert self.column_transformer != None
        return self.column_transformer.get_feature_names_out()


class CategoryGrouper(BaseEstimator, TransformerMixin):
    """A tranformer for combining low count observations for categorical features.

    This transformer will preserve category values that are above a certain
    threshold, while bucketing together all the other values. This will fix issues
    where new data may have an unobserved category value that the training data
    did not have.
    """

    def __init__(self, threshold=0.05):
        """Initialize method.

        Args:
            threshold (float): The threshold to apply the bucketing when
                categorical values drop below that threshold.
        """
        self.d = defaultdict(list)
        self.threshold = threshold

    def transform(self, X, **transform_params):
        """Transforms X with new buckets.

        Args:
            X (obj): The dataset to pass to the transformer.

        Returns:
            The transformed X with grouped buckets.
        """
        X_copy = X.copy()
        for col in X_copy.columns:
            X_copy[col] = X_copy[col].apply(
                lambda x: x if x in self.d[col] else 'CategoryGrouperOther')
        return X_copy

    def fit(self, X, y=None, **fit_params):
        """Fits transformer over X.

        Builds a dictionary of lists where the lists are category values of the
        column key for preserving, since they meet the threshold.
        """
        df_rows = len(X.index)
        for col in X.columns:
            calc_col = X.groupby(col)[col].agg(
                lambda x: (len(x) * 1.0) / df_rows)
            self.d[col] = calc_col[calc_col >= self.threshold].index.tolist()
        return self


class NoShowPreprocessing(BaseEstimator, TransformerMixin):
    """NoShow dataset preprocessing transformer
    """

    def __init__(self):
        pass

    def data_cleaning(self, X):
        """ Convert all string to lower and remap errorous categories
        """
        # X = X.applymap(lambda s: s.lower() if type(
        #     s) == str else s)  # convert all string to lower
        # remap errorous categories

        return X

    def feature_engineer(self, X):
        return X

    def preprocess(self, X):
        """Impute numeric features with mean and cat features with most_frequent cat
        """
        return X

    def get_cat_col(self, X):
        """Get categories columns of dataframe

        Args:
            X (Dataframe): dataframe

        Returns:
            List(String): List of categories columns
        """
        return X.select_dtypes(
            include=['object', 'category']).columns.tolist()

    def get_num_col(self, X):
        """Get numeric columns of dataframe

        Args:
            X (Dataframe): dataframe

        Returns:
            List(String): List of numeric columns
        """
        return X.select_dtypes(
            include=['int64', 'float64']).columns.tolist()

    def postprocess(self, X):
        """Label encoding cat feature
        """
        # Get categorical columns
        categorical_cols = self.get_cat_col(X)
        # Encode category columns
        le = defaultdict(LabelEncoder)
        X[categorical_cols] = X[categorical_cols].apply(
            lambda x: le[x.name].fit_transform(x))

        return X

    def fit(self, X, y=None):
        self.is_fitted_ = True
        return self

    def transform(self, X, y=None):
        check_is_fitted(self, 'is_fitted_')

        X = self.data_cleaning(X)
        X = self.preprocess(X)
        X = self.feature_engineer(X)
        X = self.postprocess(X)

        X = check_array(X, accept_sparse=True)

        return X
