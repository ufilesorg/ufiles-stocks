from apps.stocks.routes import router as stocks_router
from apps.stocks.routes import stock_image_router
from fastapi_mongo_base.core import app_factory

from . import config

app = app_factory.create_app(settings=config.Settings())

app.include_router(stocks_router, prefix=f"{config.Settings.base_path}")
app.include_router(stock_image_router, prefix=f"{config.Settings.base_path}")
