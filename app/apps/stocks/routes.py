import logging
from typing import Literal

import fastapi
from fastapi import BackgroundTasks, Query
from fastapi_mongo_base.core import exceptions
from fastapi_mongo_base.routes import AbstractTaskRouter
from server.config import Settings
from usso import UserData
from usso.fastapi.integration import jwt_access_security

from .freepik import FreePikManager
from .models import StockImageDownload
from .schemas import (
    StockImage,
    StockImageCreateSchema,
    StockImageDownloadSchema,
    StockImageRequest,
)
from .shutterstock import ShutterStockManager


class StockImageRouter(
    AbstractTaskRouter[StockImageDownload, StockImageDownloadSchema]
):
    def __init__(self):
        super().__init__(
            model=StockImageDownload,
            schema=StockImageDownloadSchema,
            user_dependency=jwt_access_security,
            tags=["Stock Images"],
            prefix="/stocks",
        )

    def config_routes(self, **kwargs):
        self.router.add_api_route(
            "/",
            self.list_items,
            methods=["GET"],
            response_model=self.list_response_schema,
            status_code=200,
        )
        self.router.add_api_route(
            "/{uid:uuid}",
            self.retrieve_item,
            methods=["GET"],
            response_model=self.retrieve_response_schema,
            status_code=200,
        )
        self.router.add_api_route(
            "/",
            self.create_item,
            methods=["POST"],
            response_model=self.create_response_schema,
            status_code=201,
            summary="Create Stock Image Request",
            # description="Create a new stock image download request item.",
        )

    async def create_item(
        self,
        request: fastapi.Request,
        data: StockImageCreateSchema,
        background_tasks: BackgroundTasks,
    ):
        """
        Create a new stock image download request item.

        ## Args:
            provider: The stock image source name.
            code: The stock image code or id.

        ## Returns:
            StockImageDownload: The created stock image item.
        """
        item = await StockImageDownload.get_by_provider_code(data.provider, data.code)
        if item:
            user_id = await self.get_user_id(request)
            new_item = await item.copy_for_user(user_id)
            return new_item

        item: StockImageDownload = await super().create_item(
            request, data.model_dump(), background_tasks
        )
        background_tasks.add_task(item.start_processing)
        return item


stock_image_router = StockImageRouter().router
router = fastapi.APIRouter(
    tags=["Stock images"],
    prefix="",
    responses={404: {"description": "Not Found"}},
    # dependencies=[Depends(jwt_access_security)],
)


@router.get("/{provider}/search", response_model=list[StockImage])
async def search(
    request: fastapi.Request,
    provider: Literal["freepik", "shutterstock"],
    q: str,
    page: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=Settings.page_max_limit),
    _: UserData = fastapi.Depends(jwt_access_security),
):
    params = dict(request.query_params)
    params["page"] = page
    params["limit"] = limit
    # logging.info(f"search params: {params}")
    try:
        match provider:
            case "freepik":
                return await FreePikManager().search(**params)
            case "shutterstock":
                return await ShutterStockManager().search(**params)
            case _:
                raise exceptions.BaseHTTPException(
                    status_code=400,
                    error="Bad Request",
                    message=f"Unknown provider {provider}",
                )

    except Exception as e:
        logging.error(f"image query: {e}")

        raise exceptions.BaseHTTPException(
            status_code=500,
            error="Bad Request",
            message=f"Could not create your request. {e}",
        )


@router.post("/{provider}/download")
async def download_image(
    request: fastapi.Request,
    provider: Literal["freepik", "shutterstock"],
    code: StockImageRequest,
    user: UserData = fastapi.Depends(jwt_access_security),
):
    match provider:
        case "freepik":
            return await FreePikManager().download(code.id, user_id=user.uid)
        case "shutterstock":
            return await ShutterStockManager().download(code.id, user_id=user.uid)
        case _:
            raise exceptions.BaseHTTPException(
                status_code=400,
                error="Bad Request",
                message=f"Unknown provider {provider}",
            )


@router.get("/{provider}/download/{job_id}")
async def get_job_status(
    request: fastapi.Request,
    provider: Literal["freepik", "shutterstock"],
    job_id: str,
    user: UserData = fastapi.Depends(jwt_access_security),
):
    try:
        match provider:
            case "freepik":
                return await FreePikManager().get_job(job_id, user_id=user.uid)
            case "shutterstock":
                return await ShutterStockManager().get_job(job_id, user_id=user.uid)
            case _:
                raise exceptions.BaseHTTPException(
                    status_code=400,
                    error="Bad Request",
                    message=f"Unknown provider {provider}",
                )

    except Exception as e:
        logging.error(f"job: {e}")

        raise exceptions.BaseHTTPException(
            status_code=500,
            error="Bad Request",
            message=f"Could not create your request. {e}",
        )


@router.post("/download")
async def download(
    url: str = fastapi.Body(embed=True),
    user: UserData = fastapi.Depends(jwt_access_security),
):
    from .services import download_job

    return await download_job(url, user.uid)
