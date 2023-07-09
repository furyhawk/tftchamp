from argparse import ArgumentParser
from motor.motor_asyncio import AsyncIOMotorClient

from config import settings
from utils.parse_config import ConfigParser

args: ArgumentParser = ArgumentParser(description="TFTChamp api server")
args.add_argument(
    "-c",
    "--config",
    default="configs/challengers.json",
    type=str,
    help="config file path (default: configs/challengers.json)",
)
config = ConfigParser.from_args(args)

mongodb_client = AsyncIOMotorClient(settings.db_uri)
database = mongodb_client[settings.db_name]
