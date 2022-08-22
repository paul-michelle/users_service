from pydantic import BaseSettings


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
