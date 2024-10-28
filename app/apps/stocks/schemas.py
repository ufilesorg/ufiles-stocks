from enum import Enum

from fastapi_mongo_base.schemas import OwnedEntitySchema
from fastapi_mongo_base.tasks import TaskMixin
from pydantic import BaseModel, Field


class StockImageProvider(str, Enum):
    shutterstock = "shutterstock"
    adobestock = "adobestock"
    freepik = "freepik"
    alamy = "alamy"
    depositphotos = "depositphotos"
    dreamstime = "dreamstime"
    envato_elements = "envato_elements"
    istockphoto = "istockphoto"
    rf123 = "123rf"
    vecteezy = "vecteezy"
    vectorstock = "vectorstock"
    yellowimages = "yellowimages"
    motionarray = "motionarray"


class StockBaseImage(BaseModel):
    url: str
    width: int
    height: int


class StockImage(BaseModel):
    id: int
    original: StockBaseImage
    preview: StockBaseImage


class StockImageRequest(BaseModel):
    id: int


class StockImageDownloadSchema(TaskMixin, OwnedEntitySchema):
    provider: StockImageProvider
    code: int
    image_url: str | None = None
    job_id: str | None = None
    status: str | None = None


class StockImageCreateSchema(BaseModel):
    provider: StockImageProvider = Field(
        ...,
        description="The stock image source. Choose one from the list of available providers.",
    )
    code: int = Field(..., description="Unique code associated with the stock image.")
