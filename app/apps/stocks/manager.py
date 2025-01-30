import asyncio
import base64
import hashlib
import hmac

from fastapi_mongo_base.utils.aionetwork import aio_request
from server.config import Settings
from singleton import Singleton

from .decodl import Decodl
from .schemas import StockImage
from .services import check_job, download


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
        self.decodl = Decodl(
            app_secret=Settings.DECODL_APP_SECRET,
            app_key=Settings.DECODL_APP_KEY,
            username=Settings.DECODL_USERNAME,
            password=Settings.DECODL_PASSWORD,
        )

        self.imgproxy_key = Settings.IMGPROXY_KEY
        self.imgproxy_salt = Settings.IMGPROXY_SALT

    def sign_imgproxy_url(self, path: str) -> str:
        key_binary = bytes.fromhex(self.imgproxy_key)
        salt_binary = bytes.fromhex(self.imgproxy_salt)
        signature = hmac.new(
            key_binary, msg=salt_binary + path.encode(), digestmod=hashlib.sha256
        ).digest()
        return base64.urlsafe_b64encode(signature).rstrip(b"=").decode()

    def get_proxied_url(self, url: str, width: int = 0, height: int = 0) -> str:
        path = f"/resize:fit:{width}:{height}/plain/{url}"
        signature = self.sign_imgproxy_url(path)
        return f"{Settings.IMGPROXY_URL}/{signature}{path}"

    async def get_row(self, row: dict, **kwargs) -> StockImage:
        raise NotImplementedError

    def get_search_params(
        self, q: str, page: int = 1, limit: int = 20, sort="newest", **kwargs
    ) -> dict:
        raise NotImplementedError

    async def search(self, q: str, page: int = 1, limit: int = 20, **kwargs):
        page = max(1, page)
        limit = max(1, min(20, limit))
        params = self.get_search_params(q=q, page=page, limit=limit, **kwargs)

        res = await aio_request(
            url=self.base_url,
            headers=self.headers,
            params=params,
        )
        stock_image_tasks = [self.get_row(row) for row in res["data"]]
        stock_images = await asyncio.gather(*stock_image_tasks)

        return stock_images

    async def download(self, code: int, user_id: str, **kwargs):
        return await download(self.decodl, self.provider, code, user_id, **kwargs)

    async def get_job(self, job_id, user_id, **kwargs):
        response = await self.decodl.get_job(job_id)
        check_job(response, job_id, user_id, **kwargs)
        return response
