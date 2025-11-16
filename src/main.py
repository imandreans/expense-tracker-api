from fastapi import FastAPI
# from .database.core import connect_db
from .api import register_routers
from .logging import configure_logging, LogLevels

configure_logging(LogLevels.info)

api = FastAPI()
register_routers(api)