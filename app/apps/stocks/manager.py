import asyncio

import aiohttp
from server.config import Settings
from singleton import Singleton
from utils.aionetwork import aio_request_session

from .schemas import StockImage


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
        self.DECODL_APP_SECRET = Settings.DECODL_APP_SECRET
        self.DECODL_APP_KEY = Settings.DECODL_APP_KEY

    async def get_row(
        self, row: dict, session: aiohttp.ClientSession = None
    ) -> StockImage:
        raise NotImplementedError

    def get_search_params(
        self, q: str, page: int = 1, limit: int = 20, sort="newest", **kwargs
    ) -> dict:
        raise NotImplementedError

    async def search(self, q: str, page: int = 1, limit: int = 20, **kwargs):
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
            "authorization": f"Bearer {self.DECODL_APP_SECRET}",
            "x-app-key": self.DECODL_APP_KEY,
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

    def check_decodl_token(self):
        import time

        import jwt

        try:
            decoded = jwt.decode(
                self.DECODL_APP_SECRET, options={"verify_signature": False}
            )
            if decoded["exp"] < time.time():
                return False
            return True
        except jwt.exceptions.DecodeError:
            return False

    async def refresh_decodl_token(self):
        import requests

        cookies = {
            "_yngt_iframe": "1",
            "_yngt": "bc81e267-ba93-4de7-9c61-ffc370ee8cbe",
            "_ga": "GA1.1.1188238991.1725189909",
            "_gcl_au": "1.1.624116689.1725189909",
            "analytics_token": "fae687f5-420f-2019-bcae-1a3f4b07c805",
            "LOCALIZE_DEFAULT_LANGUAGE": "fa",
            "xDatePickerLocale": "fa",
            "G_ENABLED_IDPS": "google",
            "xClientVersion": "5.62.1",
            "analytics_session_token": "63c1a379-7b2f-aa05-b6b6-19e4f998df8d",
            "yektanet_session_last_activity": "9/28/2024",
            "xAccessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjdGNzI0NDNFLUYzNkItMTQxMC04MTI2LTAwQkIyNkNBRjExMiIsInVzZXJuYW1lIjoibWFoZGlraWFuaSIsInNjb3BlcyI6WyJCQVNJQyIsIkRFVkVMT1AiXSwiaXNBY3RpdmUiOnRydWUsImhlYWRpbmdJZCI6IkQ1MTYyMTQ5LUIwMzktNEFBMy05NjE5LTRCQjU2QjVGMzg1MCIsImlhdCI6MTcyNzUzNTg5NywiZXhwIjoxNzI3NjIyMjk3fQ.LKztVajTlrX01gs-jQcbLNusKwanXfiy89b4to6C0Bs",
            "xRefreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjdGNzI0NDNFLUYzNkItMTQxMC04MTI2LTAwQkIyNkNBRjExMiIsInVzZXJuYW1lIjoibWFoZGlraWFuaSIsInNjb3BlcyI6WyJCQVNJQyIsIkRFVkVMT1AiXSwiaXNBY3RpdmUiOnRydWUsImhlYWRpbmdJZCI6IkQ1MTYyMTQ5LUIwMzktNEFBMy05NjE5LTRCQjU2QjVGMzg1MCIsImlhdCI6MTcyNzUzNTg5NywiZXhwIjoxNzMwMTI3ODk3fQ.pj8T1OvSAys1-h-R3tT0aZIQ0aAtfPXobO7zntSatc0",
            "_ga_NFWH4DC7BN": "GS1.1.1727535880.5.1.1727536595.0.0.0",
            "_ga_2E5D7KST1N": "GS1.1.1727535880.14.1.1727536596.0.0.0",
        }

        headers = {
            "accept": "application/json",
            "accept-language": "fa",
            "content-type": "application/json",
            # 'cookie': '_yngt_iframe=1; _yngt=bc81e267-ba93-4de7-9c61-ffc370ee8cbe; _ga=GA1.1.1188238991.1725189909; _gcl_au=1.1.624116689.1725189909; analytics_token=fae687f5-420f-2019-bcae-1a3f4b07c805; LOCALIZE_DEFAULT_LANGUAGE=fa; xDatePickerLocale=fa; G_ENABLED_IDPS=google; xClientVersion=5.62.1; analytics_session_token=63c1a379-7b2f-aa05-b6b6-19e4f998df8d; yektanet_session_last_activity=9/28/2024; xAccessToken=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjdGNzI0NDNFLUYzNkItMTQxMC04MTI2LTAwQkIyNkNBRjExMiIsInVzZXJuYW1lIjoibWFoZGlraWFuaSIsInNjb3BlcyI6WyJCQVNJQyIsIkRFVkVMT1AiXSwiaXNBY3RpdmUiOnRydWUsImhlYWRpbmdJZCI6IkQ1MTYyMTQ5LUIwMzktNEFBMy05NjE5LTRCQjU2QjVGMzg1MCIsImlhdCI6MTcyNzUzNTg5NywiZXhwIjoxNzI3NjIyMjk3fQ.LKztVajTlrX01gs-jQcbLNusKwanXfiy89b4to6C0Bs; xRefreshToken=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjdGNzI0NDNFLUYzNkItMTQxMC04MTI2LTAwQkIyNkNBRjExMiIsInVzZXJuYW1lIjoibWFoZGlraWFuaSIsInNjb3BlcyI6WyJCQVNJQyIsIkRFVkVMT1AiXSwiaXNBY3RpdmUiOnRydWUsImhlYWRpbmdJZCI6IkQ1MTYyMTQ5LUIwMzktNEFBMy05NjE5LTRCQjU2QjVGMzg1MCIsImlhdCI6MTcyNzUzNTg5NywiZXhwIjoxNzMwMTI3ODk3fQ.pj8T1OvSAys1-h-R3tT0aZIQ0aAtfPXobO7zntSatc0; _ga_NFWH4DC7BN=GS1.1.1727535880.5.1.1727536595.0.0.0; _ga_2E5D7KST1N=GS1.1.1727535880.14.1.1727536596.0.0.0',
            "origin": "https://decodl.net",
            "priority": "u=1, i",
            "referer": "https://decodl.net/fa/auth/login",
            "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            "x-client-id": "",
            "x-client-version": "5.62.1",
        }

        json_data = {
            "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjdGNzI0NDNFLUYzNkItMTQxMC04MTI2LTAwQkIyNkNBRjExMiIsInVzZXJuYW1lIjoibWFoZGlraWFuaSIsInNjb3BlcyI6WyJCQVNJQyIsIkRFVkVMT1AiXSwiaXNBY3RpdmUiOnRydWUsImhlYWRpbmdJZCI6IkQ1MTYyMTQ5LUIwMzktNEFBMy05NjE5LTRCQjU2QjVGMzg1MCIsImlhdCI6MTcyNzUzNTg5NywiZXhwIjoxNzMwMTI3ODk3fQ.pj8T1OvSAys1-h-R3tT0aZIQ0aAtfPXobO7zntSatc0",
        }

        response = requests.post(
            "https://decodl.net/api/auth/refresh",
            cookies=cookies,
            headers=headers,
            json=json_data,
        )

        # Note: json_data will not be serialized by requests
        # exactly as it was in the original request.
        # data = '{"refreshToken":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjdGNzI0NDNFLUYzNkItMTQxMC04MTI2LTAwQkIyNkNBRjExMiIsInVzZXJuYW1lIjoibWFoZGlraWFuaSIsInNjb3BlcyI6WyJCQVNJQyIsIkRFVkVMT1AiXSwiaXNBY3RpdmUiOnRydWUsImhlYWRpbmdJZCI6IkQ1MTYyMTQ5LUIwMzktNEFBMy05NjE5LTRCQjU2QjVGMzg1MCIsImlhdCI6MTcyNzUzNTg5NywiZXhwIjoxNzMwMTI3ODk3fQ.pj8T1OvSAys1-h-R3tT0aZIQ0aAtfPXobO7zntSatc0"}'
        # response = requests.post('https://decodl.net/api/auth/refresh', cookies=cookies, headers=headers, data=data)

    async def update_decodl(self):
        cookies = {
            "xAccessToken": Settings.DECODL_ACCESS_TOKEN,
            "xRefreshToken": Settings.DECODL_REFRESH_TOKEN,
        }
        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {Settings.DECODL_ACCESS_TOKEN}",
        }
        params = {
            "reset": "true",
            "customErrorHandle": "false",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://decodl.net/api/auth/application/decodl/token",
                params=params,
                cookies=cookies,
                headers=headers,
            ) as response:
                # if not response.ok:
                #     return None
                res = await response.json()
                return res["accessToken"]

    async def get_job(self, job_id):
        async with aiohttp.ClientSession() as session:
            headers = {
                "Content-Type": "application/json",
                "authorization": f"Bearer {self.DECODL_APP_SECRET}",
                "x-app-key": self.DECODL_APP_KEY,
            }
            url = f"https://decodl.net/api/job/dev/{job_id}"
            res = await aio_request_session(session=session, url=url, headers=headers)
            import logging

            logging.info(f"get_job: {res}")
            # res.pop("balance", None)

            return res
