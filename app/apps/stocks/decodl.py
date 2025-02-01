import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
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
        # self.base_url = "https://decodl.net/api"
        self.base_url = "https://decodl.ir/api"
        self.proxy = os.getenv("IR_PROXY")

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

    @asynccontextmanager
    async def get_client(
        self, headers: dict = None
    ) -> AsyncGenerator[httpx.AsyncClient, None]:
        client = httpx.AsyncClient(
            proxy=self.proxy, base_url=self.base_url, headers=headers
        )
        try:
            yield client
        finally:
            await client.aclose()

    def __repr__(self) -> str:
        import json

        return json.dumps(self.__dict__, indent=4)

    async def login(self):
        if self.username is None or self.password is None:
            raise ValueError("Must provide username and password to login")

        data = {
            "username": self.username,
            "password": self.password,
            "scopes": [
                "BASIC",
            ],
        }
        async with self.get_client() as client:
            response = await client.post("/auth/login", json=data)
            response.raise_for_status()
            response_json: dict = response.json()
            self.refresh_token = response_json.get("refreshToken")
            self.access_token = response_json.get("accessToken")

    async def refresh(self):
        cookies = {
            "xAccessToken": self.access_token,
            "xRefreshToken": self.refresh_token,
        }
        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {self.access_token}",
        }
        async with self.get_client(headers=headers) as client:
            response = await client.post("/auth/refresh")  # , cookies=cookies)
            response.raise_for_status()
            response_json: dict = response.json()
            self.access_token = response_json.get("accessToken")

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
        async with httpx.AsyncClient(proxy=self.proxy) as client:
            response = await client.post(
                f"{self.base_url}/auth/application/decodl/token",
                # cookies=cookies,
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            response_json: dict = response.json()
            self.app_key = response_json.get("appCredential", {}).get("clientId", {})
            self.app_secret = response_json.get("accessToken")

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

        data = {"code": str(code), "providerName": provider}
        async with self.get_client(headers=await self.get_headers()) as client:
            response = await client.post("/product/dev", json=data)
            response.raise_for_status()
            response_json: dict = response.json()
            return response_json

    async def get_job(self, job_id):
        async with self.get_client(headers=await self.get_headers()) as client:
            response = await client.get(f"/job/dev/{job_id}")
            response.raise_for_status()
            response_json: dict = response.json()
            return response_json

    async def get_cost(self, code: int, provider: str):
        data = {
            "code": str(code),
            "link": "",
            "options": [
                {
                    "name": "",
                    "value": "",
                },
            ],
            "providerName": provider,
        }

        async with self.get_client(headers=await self.get_headers()) as client:
            response = await client.post("/product/dev/info", json=data)
            response.raise_for_status()
            response_json: dict = response.json()
            return response_json


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
