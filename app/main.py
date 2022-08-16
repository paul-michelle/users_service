import logging
from starlette.exceptions import HTTPException
from fastapi import FastAPI
from fastapi.exception_handlers import http_exception_handler

from app.routers import auth, users, files

logger = logging.getLogger(name=__name__)

app = FastAPI()

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(files.router)


@app.exception_handler(HTTPException)
async def log_http_exception(request, exc):
    logger.error('Exception ocurred: %s', repr(exc))
    return await http_exception_handler(request, exc)
