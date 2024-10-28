import os

from fastapi_mongo_base._utils.aionetwork import aio_request
from singleton import Singleton


class Decodl(metaclass=Singleton):

    def __init__(
        self,
        *,
        app_secret: str = os.getenv("DECODL_APP_SECRET"),
        app_key: str = os.getenv("DECODL_APP_KEY"),
        username: str = os.getenv("DECODL_USERNAME"),
        password: str = os.getenv("DECODL_PASSWORD"),
        refresh_token: str = os.getenv("DECODL_REFRESH_TOKEN"),
        access_token: str = os.getenv("DECODL_ACCESS_TOKEN"),
    ):
        self.base_url = "https://decodl.net/api"

        if (
            (app_key is None or app_secret is None)
            and (username is None or password is None)
            and (access_token is None or refresh_token is None)
        ):
            raise ValueError(
                "Must provide either refresh_token, or app_key and app_secret, or username and password"
            )

        self.app_secret = app_secret
        self.app_key = app_key
        self.username = username
        self.password = password
        self.refresh_token = refresh_token
        self.access_token = access_token

    def is_secret_valid(self):
        import time

        import jwt

        if self.app_key is None or self.app_secret is None:
            return False

        try:
            decoded = jwt.decode(self.app_secret, options={"verify_signature": False})
            if decoded.get("exp", time.time() - 10) < time.time():
                return False
            return True
        except jwt.exceptions.DecodeError:
            return False

    async def get_headers(self):
        if not self.is_secret_valid():
            await self.login()
            await self.get_api_key()

        return {
            "Accept-Language": "en-US",
            "Accept": "application/json",
            "authorization": f"Bearer {self.app_secret}",
            "x-app-key": self.app_key,
        }

    def __repr__(self) -> str:
        import json

        return json.dumps(self.__dict__, indent=4)

    async def login(self):
        if self.username is None or self.password is None:
            raise ValueError("Must provide username and password to login")

        login_url = f"{self.base_url}/auth/login"
        data = {
            "username": self.username,
            "password": self.password,
            "scopes": [
                "BASIC",
            ],
        }
        response = await aio_request(method="post", url=login_url, json=data)
        self.refresh_token = response.get("refreshToken")
        self.access_token = response.get("accessToken")

    async def refresh(self):
        cookies = {
            "xAccessToken": self.access_token,
            "xRefreshToken": self.refresh_token,
        }
        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {self.access_token}",
        }
        refresh_url = f"{self.base_url}/auth/refresh"
        response = await aio_request(
            method="post", url=refresh_url, cookies=cookies, headers=headers
        )
        self.access_token = response.get("accessToken")

    async def get_api_key(self):
        cookies = {
            "xAccessToken": self.access_token,
            # "xRefreshToken": self.refresh_token,
        }
        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {self.access_token}",
        }
        params = {
            "reset": "true",
            "customErrorHandle": "false",
        }
        # 'https://decodl.net/api/auth/application/decodl/token?reset=false&customErrorHandle=true'
        response = await aio_request(
            method="post",
            url=f"{self.base_url}/auth/application/decodl/token",
            # cookies=cookies,
            headers=headers,
            params=params,
        )
        self.app_key = response.get("appCredential", {}).get("clientId", {})
        self.app_secret = response.get("accessToken")

    async def download(self, provider: str, code: int):
        if provider not in [
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

        url = f"{self.base_url}/product/dev"
        headers = await self.get_headers()
        data = {"code": str(code), "providerName": provider}
        response = await aio_request(method="post", url=url, headers=headers, json=data)
        return response

    async def get_job(self, job_id):
        url = f"{self.base_url}/job/dev/{job_id}"
        headers = await self.get_headers()
        response = await aio_request(method="get", url=url, headers=headers)
        return response


if __name__ == "__main__":
    import asyncio
    import os

    import dotenv

    async def main():
        dotenv.load_dotenv()
        deco = Decodl(
            app_secret=None,
            app_key=None,
            username=os.getenv("DECODL_USERNAME"),
            password=os.getenv("DECODL_PASSWORD"),
        )
        try:
            await deco.login()
            print("login")
            # await deco.refresh()
            print("refresh")
            await deco.get_api_key()
            print("get_api_key")
        except Exception as e:
            print(e)
        return deco

    self = asyncio.run(main())
