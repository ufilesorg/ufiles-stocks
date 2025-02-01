import asyncio
import json
import logging
import uuid
from datetime import datetime
from io import BytesIO
from urllib.parse import urlparse

import ufiles
from fastapi_mongo_base.utils import aionetwork, basic, texttools
from server.config import Settings

from .decodl import Decodl
from .schemas import StockImageProvider


@basic.try_except_wrapper
async def upload_image(
    image_bytes: BytesIO,
    user_id: uuid.UUID,
    filename: str = None,
    file_upload_dir: str = "stock photos",
):
    now = datetime.now()
    image_name = (
        texttools.sanitize_filename(filename)
        if filename
        else f"stock_photo {now:%y.%2m.%2d}"
    )
    # image_bytes = imagetools.convert_to_webp_bytes(image)
    image_bytes.name = f"{image_name}.webp"
    async with ufiles.AsyncUFiles(
        ufiles_base_url=Settings.UFILES_BASE_URL,
        usso_base_url=Settings.USSO_BASE_URL,
        api_key=Settings.UFILES_API_KEY,
    ) as client:
        uploaded = await client.upload_bytes(
            image_bytes,
            filename=f"{file_upload_dir}/{image_bytes.name}",
            public_permission=json.dumps({"permission": ufiles.PermissionEnum.READ}),
            user_id=str(user_id),
            meta_data={
                "filename": filename,
            },
        )

    return uploaded


async def download(
    decodl: Decodl, provider: StockImageProvider, code: int, user_id: str, **kwargs
):
    response = await decodl.download(provider, code)
    job_id = response.get("jobId")
    asyncio.create_task(update_dl_job(decodl, job_id, user_id, **kwargs))
    return response


@basic.try_except_wrapper
async def download_job(url, user_id, **kwargs):
    job_bytes = await aionetwork.aio_request_binary(url=url)
    # image = Image.open(job_bytes)
    url_path_parts = urlparse(url).path.split("/")
    filename = kwargs.get(
        "prompt",
        kwargs.get(
            "filename",
            url_path_parts[-2] if len(url_path_parts) > 1 else "stock_photo",
        ),
    )

    await upload_image(job_bytes, user_id=user_id, filename=filename)


async def check_job(response: dict, job_id: str, user_id, **kwargs):
    progress = response.get("progress", 0)
    if progress == 100 and "downloadLink" in response:
        logging.info(f"Downloading job {user_id=} {job_id=}")
        return await download_job(response["downloadLink"], user_id, **kwargs)


@basic.try_except_wrapper
@basic.delay_execution(Settings.update_time)
async def update_dl_job(decodl: Decodl, job_id, user_id, **kwargs):
    response = await decodl.get_job(job_id)
    if response.get("error") == "error":
        logging.error(f"Error downloading image from decodl: {response}")
        return

    if response.get("progress") == 100:
        logging.info(f"Image downloaded from decodl: {response}")
        return await check_job(response, job_id, user_id, **kwargs)

    asyncio.create_task(update_dl_job(decodl, job_id, user_id, **kwargs))
