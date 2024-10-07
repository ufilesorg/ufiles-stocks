import asyncio
import os
import random

import aiohttp
from apps.stocks.schema import StockBaseImage, StockImage
from utils.aionetwork import aio_request, aio_request_session


async def get_freepik(row: dict, session: aiohttp.ClientSession = None):
    id = row.get("id")
    await asyncio.sleep(random.uniform(0.1, 0.3))
    url = f"https://api.freepik.com/v1/resources/{id}"
    headers = {
        "Accept-Language": "en-US",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Freepik-API-Key": os.getenv("FREEPIK_API_KEY"),
    }
    if session is None:
        response = await aio_request(url=url, headers=headers)
    else:
        response = await aio_request_session(session=session, url=url, headers=headers)

    freepik_object = StockImage(
        id=id,
        original=StockBaseImage(
            url=response.get("data", {}).get("url"),
            width=response.get("data", {}).get("dimensions", {}).get("width", 1),
            height=response.get("data", {}).get("dimensions", {}).get("height", 1),
        ),
        preview=StockBaseImage(
            url=response.get("data", {}).get("preview", {}).get("url"),
            width=response.get("data", {}).get("preview", {}).get("width", 1),
            height=response.get("data", {}).get("preview", {}).get("height", 1),
        ),
    )
    return freepik_object
