# from argparse import ArgumentParser
from logging import Logger
import uuid
import os
import pickle
import sys
from typing import Any, List, Optional
from pydantic import BaseModel, Field
from logging.config import dictConfig

# import wrappers
# import pandas as pd
# import matplotlib.pyplot as plt

# import logging
from utils.logger import logging

from config import LogConfig, get_settings

# from utils.parse_config import ConfigParser

from dependencies import config, mongodb_client, database


class MongoBaseModel(BaseModel):
    id: str = Field(
        default_factory=uuid.uuid4,
        alias="_id",
        examples=[
            "NA1_4387530978-wgvrKfcuCGDmgyrUmiXknS41acg6Y26hfQwsXNj_eJ86Tv8_Bb7SBOUVSQqI1JdyBSmq92XGDrGYHA"
        ],
    )


class FeatureImportanceOutput(BaseModel):
    results: List[dict] = []
    # label: List[str] = []
    # feature_importance: List[float] = []


class MetadataOutput(BaseModel):
    latest_version: str = Field(
        ..., examples=["12.15.458.1416"], title="The latest_version Schema"
    )
    latest_patch: str = Field(
        ..., examples=["2022-08-10"], title="The latest_patch Schema"
    )


class ImagesList(BaseModel):
    results: List[dict] = []


class Text(MongoBaseModel):
    text: str = Field(..., examples=["Description"], title="The text Schema")


class Image(Text):
    image: bytes = Field(..., examples=[None], title="The Image Schema")


class PredictionInput(BaseModel):
    text: str
    reference: str
    modelId: str


class PredictionOutput(BaseModel):
    summarized: str
    metrics: str


class Predictor:
    config: Optional[Any]
    model: Optional[Any]
    targets: Optional[List[str]]

    def __init__(self) -> None:
        # args: ArgumentParser = ArgumentParser(
        #     description='TFTChamp api server')
        # args.add_argument('-c', '--config', default='configs/challengers.json', type=str,
        #                   help='config file path (default: configs/challengers.json)')
        # config = ConfigParser.from_args(args)

        dictConfig(LogConfig().dict())
        logger: Logger = logging.getLogger("app")
        self.logger: Logger = logger
        self.config = config

    def get_default_parameters(
        self, platform=None, league=None, version=None, patch=None
    ):
        if platform is None:
            platform = self.config["server"]
        if league is None:
            league = self.config["league"]
        if version is None:
            version = self.config["latest_release"]
        if patch is None:
            patch = self.config["patch"]

        return platform, league, version, patch

    async def load_model(
        self, platform=None, league=None, version=None, patch=None
    ) -> None:
        """Loads the model"""
        self.logger.info("Preloading pipleine")
        platform, league, version, patch = self.get_default_parameters(
            platform, league, version, patch
        )

        # https://stackoverflow.com/questions/2121874/python-pickling-after-changing-a-modules-directory/2121918#2121918
        sys.path.append(r"../pipeline")
        # load the model from db
        prefix: str = f"{platform}_{league}_{version}_{patch}_model"
        if (
            binary := await database[f"{prefix}"].find_one({"_id": f"{prefix}"})
        ) is not None:
            binary_model = binary["model"]
            loaded_model = pickle.loads(binary_model)
            self.logger.info(loaded_model)
            self.model = loaded_model
            return

        # load the model from disk
        if self.config["model_dir"]:
            load_path = os.path.join(self.config["model_dir"], "model.pkl")
        else:
            load_path = os.path.join(self.save_dir, "model.pkl")

        self.logger.info(f"Loading model from: {load_path}")

        with open(load_path, "rb") as input_file:
            loaded_model = pickle.load(input_file)
            self.logger.info(loaded_model)
        self.model = loaded_model

    async def get_feature_importance(
        self, platform=None, league=None, version=None, patch=None
    ):
        await self.load_model(platform, league, version, patch)

        if hasattr(self.model[-1], "feature_importances_"):
            self.logger.info("start get_feature_importance")
            feature_names = self.model["column_transformer"].get_feature_names_out()

            # numpy object to python primitive
            feature_importances_list = self.model[-1].feature_importances_.tolist()
            feature_importances = []
            for index, feature_name in enumerate(feature_names):
                feature_importances.append(
                    {
                        "label": feature_name,
                        "feature_importance": feature_importances_list[index],
                    }
                )

            self.logger.info("built get_feature_importance")
            top_feature_importances = sorted(
                feature_importances, key=lambda d: d["feature_importance"], reverse=True
            )[:100]
            self.logger.info("sorted get_feature_importance")

            return top_feature_importances
            # return self.model[-1].feature_importances_[-50:].tolist(), feature_names[-50:].tolist()
        else:
            return []

    def predict(self, input: PredictionInput) -> PredictionOutput:
        """Predict input(x) to (y)"""
        if not self.model:
            raise RuntimeError("Model is not loaded")

        self.logger.info(input)


# Create Singleton
tft_champ_model: Predictor = Predictor()


def get_model() -> Predictor:
    return tft_champ_model
