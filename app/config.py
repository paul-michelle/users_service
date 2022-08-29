from typing import Optional

from pydantic import BaseSettings
from sqlalchemy.engine.url import URL


class Settings(BaseSettings):
    secret_key        : str
    algo              : Optional[str] = "HS256"
    admin_key         : str
    
    postgres_user     : str
    postgres_password : str
    postgres_host     : str
    postgres_port     : str
    postgres_database : str
    
    class Config:
        env_file = '.env'


settings = Settings()

def get_conn_url(sync: bool = False) -> URL:
    return URL.create(  # type: ignore
    drivername=f"postgresql+{'psycopg2' if sync else 'asyncpg'}",
    username=settings.postgres_user,
    password=settings.postgres_password,
    host=settings.postgres_host,
    port=settings.postgres_port,
    database=settings.postgres_database
)
