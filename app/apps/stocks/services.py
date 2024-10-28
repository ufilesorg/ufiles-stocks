import asyncio
import json
import logging
import re
import uuid
from datetime import datetime
from io import BytesIO
from urllib.parse import urlparse

from fastapi_mongo_base._utils.aionetwork import aio_request_binary
from fastapi_mongo_base._utils.basic import delay_execution, try_except_wrapper
from PIL import Image
from server.config import Settings
from usso.async_session import AsyncUssoSession
from utils import ufiles

from .decodl import Decodl
from .schemas import StockImageProvider


def sanitize_filename(name: str) -> str:
    # Remove characters not safe or meaningful in filenames, and replace spaces/hyphens with underscores
    sanitized = re.sub(r"[^a-zA-Z0-9_. ]", "", name)

    # Replace spaces and hyphens with underscores
    sanitized = re.sub(r"[ \-]", "_", sanitized)

    # Remove multiple consecutive underscores
    sanitized = re.sub(r"_+", "_", sanitized)

    # Optionally, remove leading or trailing underscores
    sanitized = sanitized.strip("_")
    position = sanitized.find("_", 80, 120)
    if position == -1:
        position = 100

    return sanitized[:position]


@try_except_wrapper
async def upload_image(
    image_bytes: BytesIO,
    user_id: uuid.UUID,
    filename: str = None,
    file_upload_dir: str = "stock photos",
):
    now = datetime.now()
    image_name = (
        sanitize_filename(filename) if filename else f"stock_photo {now:%y.%2m.%2d}"
    )
    # image_bytes = imagetools.convert_to_webp_bytes(image)
    image_bytes.name = f"{image_name}.webp"
    async with AsyncUssoSession(
        ufiles.AsyncUFiles().refresh_url,
        ufiles.AsyncUFiles().refresh_token,
    ) as client:
        return await ufiles.AsyncUFiles().upload_bytes_session(
            client,
            image_bytes,
            filename=f"{file_upload_dir}/{image_bytes.name}",
            public_permission=json.dumps({"permission": ufiles.PermissionEnum.READ}),
            user_id=str(user_id),
            meta_data={
                "filename": filename,
            },
        )


async def upload_images(
    images: list[Image.Image],
    user_id: uuid.UUID,
    filename: str,
    file_upload_dir="stock photos",
):
    image_name = sanitize_filename(filename)

    async with AsyncUssoSession(
        ufiles.AsyncUFiles().refresh_url,
        ufiles.AsyncUFiles().refresh_token,
    ) as client:
        uploaded_items = [
            await upload_image(
                client,
                images[0],
                image_name=f"{image_name}_{1}",
                user_id=user_id,
                filename=filename,
                file_upload_dir=file_upload_dir,
            )
        ]
        uploaded_items += await asyncio.gather(
            *[
                upload_image(
                    client,
                    image,
                    image_name=f"{image_name}_{i+2}",
                    user_id=user_id,
                    filename=filename,
                    file_upload_dir=file_upload_dir,
                )
                for i, image in enumerate(images[1:])
            ]
        )

    return uploaded_items


async def download(
    decodl: Decodl, provider: StockImageProvider, code: int, user_id: str, **kwargs
):
    response = await decodl.download(provider, code)
    job_id = response.get("jobId")
    asyncio.create_task(update_dl_job(decodl, job_id, user_id, **kwargs))


@try_except_wrapper
async def download_job(url, user_id, **kwargs):
    job_bytes = await aio_request_binary(url=url)
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


def check_job(response: dict, job_id: str, user_id, **kwargs):
    progress = response.get("progress", 0)
    if progress == 100 and "downloadLink" in response:
        logging.info(f"Downloading job {user_id=} {job_id=}")
        asyncio.create_task(download_job(response["downloadLink"], user_id, **kwargs))


@try_except_wrapper
@delay_execution(Settings.update_time)
async def update_dl_job(decodl: Decodl, job_id, user_id, **kwargs):
    response = await decodl.get_job(job_id)
    if response.get("error") == "error":
        logging.error(f"Error downloading image from decodl: {response}")
        return

    if response.get("progress") == 100:
        logging.info(f"Image downloaded from decodl: {response}")
        check_job(response, job_id, user_id, **kwargs)
        return

    asyncio.create_task(update_dl_job(decodl, job_id, user_id, **kwargs))
