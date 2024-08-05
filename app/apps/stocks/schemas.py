from pydantic import BaseModel


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
