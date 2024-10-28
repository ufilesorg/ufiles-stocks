import uuid

from fastapi_mongo_base.models import OwnedEntity
from pymongo import ASCENDING, IndexModel
from server.config import Settings

from .decodl import Decodl
from .schemas import StockImageDownloadSchema
from .services import download


class StockImageDownload(StockImageDownloadSchema, OwnedEntity):
    class Settings:
        indexes = OwnedEntity.Settings.indexes + [
            IndexModel([("code", ASCENDING)], unique=True),
            IndexModel([("provider", ASCENDING)], unique=True),
        ]

    @classmethod
    async def get_by_provider_code(
        cls, provider: str, code: int
    ) -> "StockImageDownload":
        return await cls.find_one({"provider": provider, "code": code})

    async def start_processing(self):
        decodl = Decodl(
            app_secret=Settings.DECODL_APP_SECRET,
            app_key=Settings.DECODL_APP_KEY,
            username=Settings.DECODL_USERNAME,
            password=Settings.DECODL_PASSWORD,
        )
        return await download(decodl, self.provider, self.code, self.user_id)

    async def copy_for_user(self, user_id: uuid.UUID, **kwargs) -> "StockImageDownload":
        new_item = self.model_copy(
            exclude=["_id"] + self.create_exclude_set(),
            update={"user_id": user_id, **kwargs},
        )
        await new_item.save()
        return new_item
