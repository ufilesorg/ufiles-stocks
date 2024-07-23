import asyncio
import random

import aiohttp
from apps.stocks.schema import StockBaseImage, StockImage
from server.config import Settings
from utils.aionetwork import aio_request, aio_request_session

from .manager import BaseStockImageManager


class FreePikManager(BaseStockImageManager):
    def __init__(self, api_key: str = Settings.FREEPIK_API_KEY):
        self.api_key = api_key
        self.base_url = "https://api.freepik.com/v1/resources"
        self.headers = {
            "Accept-Language": "en-US",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Freepik-API-Key": self.api_key,
        }
        self.provider = "freepik"

    async def get_row(self, row: dict, session: aiohttp.ClientSession = None):
        id = row.get("id")
        await asyncio.sleep(random.uniform(0.1, 0.3))
        url = f"{self.base_url}/{id}"

        if session is None:
            response = await aio_request(url=url, headers=self.headers)
        else:
            response = await aio_request_session(
                session=session, url=url, headers=self.headers
            )

        response_data: dict = response.get("data", {})

        result = StockImage(
            id=id,
            original=StockBaseImage(
                url=response_data.get("url"),
                width=response_data.get("dimensions", {}).get("width", 1),
                height=response_data.get("dimensions", {}).get("height", 1),
            ),
            preview=StockBaseImage(
                url=response_data.get("preview", {}).get("url"),
                width=response_data.get("preview", {}).get("width", 1),
                height=response_data.get("preview", {}).get("height", 1),
            ),
        )
        return result

    def get_search_params(
        self, q: str, page: int = 1, limit: int = 10, sort="latest", **kwargs
    ) -> dict:
        return {
            "locale": "en-US",
            "page": page,
            "limit": limit,
            "order": sort,
            "term": q,
        }
