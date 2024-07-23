import asyncio

import aiohttp
from apps.stocks.schema import StockImage
from server.config import Settings
from singleton import Singleton
from utils.aionetwork import aio_request_session


class BaseStockImageManager(metaclass=Singleton):
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.base_url: str = ""
        self.headers = {
            "Accept-Language": "en-US",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        self.provider = None

    async def get_row(
        self, row: dict, session: aiohttp.ClientSession = None
    ) -> StockImage:
        raise NotImplementedError

    def get_search_params(
        self, q: str, page: int = 1, limit: int = 10, sort="newest", **kwargs
    ) -> dict:
        raise NotImplementedError

    async def search(self, q: str, page: int = 1, limit: int = 10, **kwargs):
        page = max(1, page)
        limit = max(1, min(20, limit))
        params = self.get_search_params(q=q, page=page, limit=limit, **kwargs)

        async with aiohttp.ClientSession() as session:
            res = await aio_request_session(
                session=session,
                url=self.base_url,
                headers=self.headers,
                params=params,
            )
            stock_image_tasks = [self.get_row(row, session) for row in res["data"]]
            stock_images = await asyncio.gather(*stock_image_tasks)

        return stock_images

    async def download(self, code: int):
        if self.provider not in [
            "shutterstock",
            "adobestock",
            "freepik",
            "alamy",
            "depositphotos",
            "dreamstime",
            "envato_elements",
            "istockphoto",
            "123rf",
            "vecteezy",
            "vectorstock",
            "yellowimages",
            "motionarray",
        ]:
            raise NotImplementedError

        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {Settings.DECODL_APP_SECRET}",
            "x-app-key": Settings.DECODL_APP_KEY,
        }

        data = {
            "code": f"{code}",
            "providerName": self.provider,
        }

        async with aiohttp.ClientSession() as session:
            url = "https://decodl.net/api/product/dev"
            job_res: dict = await aio_request_session(
                session=session, method="post", url=url, headers=headers, json=data
            )
            return job_res

    async def get_job(self, job_id):
        async with aiohttp.ClientSession() as session:
            headers = {
                "Content-Type": "application/json",
                "authorization": f"Bearer {Settings.DECODL_APP_SECRET}",
                "x-app-key": Settings.DECODL_APP_KEY,
            }
            url = f"https://decodl.net/api/job/dev/{job_id}"
            res = await aio_request_session(session=session, url=url, headers=headers)
            import logging
            logging.info(f"get_job: {res}")
            # res.pop("balance", None)

            return res
