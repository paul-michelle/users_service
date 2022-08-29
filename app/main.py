import logging

from fastapi import FastAPI
from fastapi.exception_handlers import http_exception_handler
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.exceptions import HTTPException

from app.db.session import db
from app.routers import auth, files, users

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


@app.on_event("startup")
async def startup():
    await db.connect()
    

@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()