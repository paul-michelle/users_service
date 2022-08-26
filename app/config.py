from pydantic import BaseSettings
from sqlalchemy.engine.url import URL


class Settings(BaseSettings):
    secret_key        : str
    admin_key         : str
    postgres_user     : str
    postgres_password : str
    postgres_host     : str
    postgres_port     : str
    postgres_database : str

    class Config:
        env_file = '.env'


settings = Settings()

conn_string = URL(
    drivername="postgresql+psycopg2",
    username=settings.postgres_user,
    password=settings.postgres_password,
    host=settings.postgres_host,
    port=settings.postgres_port,
    database=settings.postgres_database
).__str__()
