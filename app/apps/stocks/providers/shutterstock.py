from server.config import Settings

from ..manager import BaseStockImageManager
from ..schemas import StockBaseImage, StockImage


class ShutterstockManager(BaseStockImageManager):
    provider = "shutterstock"

    def __init__(self, api_key: str = Settings.SHUTTERSTOCK_API_KEY):
        super().__init__(api_key)
        self.api_key = api_key
        self.base_url = "https://api.shutterstock.com/v2/images/search"
        self.headers = {
            "Accept-Language": "en-US",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    async def get_row(self, row: dict, **kwargs):
        id = row.get("id")
        # await asyncio.sleep(random.uniform(0.1, 0.3))
        assets: dict = row.get("assets", {})
        preview: dict = assets.get("preview", {})
        preview_1500: dict = assets.get("preview_1500", {})
        # f"{self.base_url}/{id}"

        result = StockImage(
            id=id,
            original=StockBaseImage(
                url=self.get_proxied_url(preview_1500.get("url"), 1500, 1500),
                width=preview_1500.get("width", 1),
                height=preview_1500.get("height", 1),
            ),
            preview=StockBaseImage(
                url=self.get_proxied_url(preview.get("url"), 1500, 1500),
                width=preview.get("width", 1),
                height=preview.get("height", 1),
            ),
        )
        return result

    def get_search_params(
        self, q: str, page: int = 1, limit: int = 10, sort="popular", **kwargs
    ) -> dict:
        return {
            "page": page,
            "per_page": limit,
            "sort": sort,
            "query": q,
        }
