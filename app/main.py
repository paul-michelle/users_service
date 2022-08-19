import logging
from starlette.exceptions import HTTPException
from fastapi import FastAPI
from fastapi.exception_handlers import http_exception_handler

from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, users, files


logger = logging.getLogger(name=__name__)

ORIGINS = ["http://127.0.0.1"]
HOSTS   = ["*"]

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=ORIGINS, max_age=300, allow_credentials=True)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=HOSTS)
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(files.router)


@app.exception_handler(HTTPException)
async def log_http_exception(request, exc):
    logger.error('Exception ocurred: %s', repr(exc))
    return await http_exception_handler(request, exc)
