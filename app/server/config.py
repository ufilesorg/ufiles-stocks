"""FastAPI server configuration."""

import dataclasses
import os
from pathlib import Path

import dotenv
from fastapi_mongo_base.core import config

dotenv.load_dotenv()


@dataclasses.dataclass
class Settings(config.Settings):
    """Server config settings."""

    base_dir: Path = Path(__file__).resolve().parent.parent
    base_path: str = "/v1/apps/stocks"
    update_time: int = 60

    FREEPIK_API_KEY: str = os.getenv("FREEPIK_API_KEY")
    SHUTTERSTOCK_API_KEY: str = os.getenv("SHUTTERSTOCK_API_KEY")
    DECODL_APP_KEY: str = os.getenv("DECODL_APP_KEY")
    DECODL_APP_SECRET: str = os.getenv("DECODL_APP_SECRET")
    DECODL_ACCESS_TOKEN: str = os.getenv("DECODL_ACCESS_TOKEN")
    DECODL_REFRESH_TOKEN: str = os.getenv("DECODL_REFRESH_TOKEN")
    DECODL_USERNAME: str = os.getenv("DECODL_USERNAME")
    DECODL_PASSWORD: str = os.getenv("DECODL_PASSWORD")

    IMGPROXY_KEY: str = os.getenv("IMGPROXY_KEY")
    IMGPROXY_SALT: str = os.getenv("IMGPROXY_SALT")
    IMGPROXY_URL: str = os.getenv("IMGPROXY_URL")

    UFILES_BASE_URL: str = os.getenv("UFILES_BASE_URL")
    USSO_BASE_URL: str = os.getenv("USSO_BASE_URL")
    UFILES_API_KEY: str = os.getenv("UFILES_API_KEY")
