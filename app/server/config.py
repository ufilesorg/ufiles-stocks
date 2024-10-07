"""FastAPI server configuration."""

import dataclasses
import logging
import logging.config
import os
from pathlib import Path

import dotenv
from singleton import Singleton

dotenv.load_dotenv()


@dataclasses.dataclass
class Settings(metaclass=Singleton):
    """Server config settings."""

    root_url: str = os.getenv("DOMAIN", default="http://localhost:8000")
    mongo_uri: str = os.getenv("MONGO_URI", default="mongodb://mongo:27017/")
    project_name: str = os.getenv("PROJECT_NAME", default="Stock Images")
    base_dir: Path = Path(__file__).resolve().parent.parent
    base_path: str = "/v1/apps/stocks"
    page_max_limit: int = 100

    app_id: str = os.getenv("APP_ID")
    app_secret: str = os.getenv("APP_SECRET")

    JWT_CONFIG: str = os.getenv(
        "USSO_JWT_CONFIG",
        default='{"jwk_url": "https://usso.io/website/jwks.json","type": "RS256","header": {"type": "Cookie", "name": "usso_access_token"} }',
    )

    FREEPIK_API_KEY: str = os.getenv("FREEPIK_API_KEY")
    SHUTTERSTOCK_API_KEY: str = os.getenv("SHUTTERSTOCK_API_KEY")
    DECODL_APP_KEY: str = os.getenv("DECODL_APP_KEY")
    DECODL_APP_SECRET: str = os.getenv("DECODL_APP_SECRET")
    DECODL_ACCESS_TOKEN: str = os.getenv("DECODL_ACCESS_TOKEN")
    DECODL_REFRESH_TOKEN: str = os.getenv("DECODL_REFRESH_TOKEN")

    testing: bool = os.getenv("TESTING", default=False)

    log_config = {
        "version": 1,
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "standard",
            },
            "file": {
                "class": "logging.FileHandler",
                "level": "INFO",
                "filename": base_dir / "logs" / "info.log",
                "formatter": "standard",
            },
        },
        "formatters": {
            "standard": {
                "format": "[{levelname} : {filename}:{lineno} : {asctime} -> {funcName:10}] {message}",
                # "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                "style": "{",
            }
        },
        "loggers": {
            "": {
                "handlers": [
                    "console",
                    "file",
                ],
                "level": "INFO",
                "propagate": True,
            }
        },
    }

    @classmethod
    def config_logger(cls):
        if not (cls.base_dir / "logs").exists():
            (cls.base_dir / "logs").mkdir()

        logging.config.dictConfig(cls.log_config)
