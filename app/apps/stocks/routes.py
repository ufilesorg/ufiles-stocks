from typing import Literal

import fastapi
from fastapi import BackgroundTasks, Query
from fastapi_mongo_base.routes import AbstractTaskRouter
from server.config import Settings
from usso import UserData
from usso.fastapi.integration import jwt_access_security
from utils import finance

from .manager import BaseStockImageManager
from .models import StockImageDownload
from .providers import freepik, shutterstock
from .schemas import (
    StockImage,
    StockImageCreateSchema,
    StockImageDownloadSchema,
    StockImageRequest,
)

__all__ = ["freepik", "shutterstock"]


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
        super().config_routes(update_route=False, delete_route=False)

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
):
    user: UserData = jwt_access_security(request)

    params = dict(request.query_params)
    params["page"] = page
    params["limit"] = limit
    # logging.info(f"search params: {params}")
    manager = BaseStockImageManager.get_child(provider)
    return await manager.search(**params)


@router.post("/{provider}/download")
async def download_image(
    request: fastapi.Request,
    provider: Literal["freepik", "shutterstock"],
    code: StockImageRequest,
):
    user: UserData = jwt_access_security(request)
    manager = BaseStockImageManager.get_child(provider)
    cost = await manager.get_cost(code.id)
    if cost.get("error"):
        raise fastapi.HTTPException(status_code=400, detail=cost.get("error"))
    cost_coin = cost.get("ratio") * Settings.decodl_ratio_coin
    await finance.check_quota(user.uid, cost_coin)
    await finance.meter_cost(user.uid, cost_coin)

    return await manager.download(code.id, user_id=user.uid)


@router.get("/{provider}/download/{job_id}")
async def get_job_status(
    request: fastapi.Request, provider: Literal["freepik", "shutterstock"], job_id: str
):
    user: UserData = jwt_access_security(request)
    manager = BaseStockImageManager.get_child(provider)
    return await manager.get_job(job_id, user_id=user.uid)


@router.get("/{provider}/cost")
async def get_cost(
    request: fastapi.Request, provider: Literal["freepik", "shutterstock"], code: int
):
    user: UserData = jwt_access_security(request)
    manager = BaseStockImageManager.get_child(provider)
    return await manager.get_cost(code)


@router.post("/download")
async def download(request: fastapi.Request, url: str = fastapi.Body(embed=True)):
    from .services import download_job

    user: UserData = jwt_access_security(request)

    return await download_job(url, user.uid)
