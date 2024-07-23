import logging
from typing import Literal

import fastapi
from apps.stocks.schema import StockImage
from core import exceptions
from usso import UserData
from usso.fastapi.integration import jwt_access_security

from .freepik import FreePikManager
from .shutterstock import ShutterStockManager
from .schema import StockImageRequest

router = fastapi.APIRouter(
    tags=["Stock images"],
    prefix="",
    responses={404: {"description": "Not Found"}},
    # dependencies=[Depends(jwt_access_security)],
)


@router.get("/{origin}/search", response_model=list[StockImage])
async def search(
    request: fastapi.Request,
    origin: Literal["freepik", "shutterstock"],
    q: str,
    _: UserData = fastapi.Depends(jwt_access_security),
):
    params = request.query_params
    logging.info(f"search params: {params}")
    try:
        match origin:
            case "freepik":
                return await FreePikManager().search(**params)
            case "shutterstock":
                return await ShutterStockManager().search(**params)
            case _:
                raise exceptions.BaseHTTPException(
                    status_code=400,
                    error="Bad Request",
                    message=f"Unknown origin {origin}",
                )

    except Exception as e:
        logging.error(f"image query: {e}")

        raise exceptions.BaseHTTPException(
            status_code=500,
            error="Bad Request",
            message=f"Could not create your request. {e}",
        )


@router.post("/{origin}/download")
async def download_image(
    request: fastapi.Request,
    origin: Literal["freepik", "shutterstock"],
    code: StockImageRequest,
    _: UserData = fastapi.Depends(jwt_access_security),
):
    try:
        match origin:
            case "freepik":
                return await FreePikManager().download(code)
            case "shutterstock":
                return await ShutterStockManager().download(code)
            case _:
                raise exceptions.BaseHTTPException(
                    status_code=400,
                    error="Bad Request",
                    message=f"Unknown origin {origin}",
                )

    except Exception as e:
        logging.error(f"image download: {e}")

        raise exceptions.BaseHTTPException(
            status_code=500,
            error="Bad Request",
            message=f"Could not create your request. {e}",
        )


@router.get("/{origin}/download/{job_id}")
async def get_job_status(
    request: fastapi.Request,
    origin: Literal["freepik", "shutterstock"],
    job_id: str,
    _: UserData = fastapi.Depends(jwt_access_security),
):
    try:
        match origin:
            case "freepik":
                return await FreePikManager().get_job(job_id)
            case "shutterstock":
                return await ShutterStockManager().get_job(job_id)
            case _:
                raise exceptions.BaseHTTPException(
                    status_code=400,
                    error="Bad Request",
                    message=f"Unknown origin {origin}",
                )

    except Exception as e:
        logging.error(f"job: {e}")

        raise exceptions.BaseHTTPException(
            status_code=500,
            error="Bad Request",
            message=f"Could not create your request. {e}",
        )
