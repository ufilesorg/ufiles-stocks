import asyncio
import json
import logging
import re
import uuid
from datetime import datetime
import aiohttp
from metisai.async_metis import AsyncMetisBot
from PIL import Image
from server.config import Settings
from usso.async_session import AsyncUssoSession
from utils import imagetools, ufiles
from fastapi_mongo_base._utils.basic import delay_execution, try_except_wrapper


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


async def upload_image(
    client: AsyncUssoSession | aiohttp.ClientSession,
    image: Image.Image,
    user_id: uuid.UUID,
    filename: str = None,
    file_upload_dir: str = "stock photos",
):
    now = datetime.now()
    image_name = (
        sanitize_filename(filename) if filename else f"stock_photo {now:%y.%2m.%2d}"
    )
    image_bytes = imagetools.convert_to_webp_bytes(image)
    image_bytes.name = f"{image_name}.webp"
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
