import logging
from starlette.exceptions import HTTPException
from fastapi import FastAPI
from fastapi.exception_handlers import http_exception_handler

from app.routers import auth, users, files

logging.basicConfig(
    filename='logs.txt',
    filemode='a',
    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
    datefmt='%H:%M:%S',
    level=logging.ERROR
)
logger = logging.getLogger(name=__name__)

app = FastAPI()

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(files.router)


@app.exception_handler(HTTPException)
async def log_http_exception(request, exc):
    logger.error('Exception ocurred: %s', repr(exc))
    return await http_exception_handler(request, exc)
