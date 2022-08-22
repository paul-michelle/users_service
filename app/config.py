from pydantic import BaseSettings


class Settings(BaseSettings):
    secret_key: str
    admin_key:  str
    

    class Config:
        env_file = '.env'


settings = Settings()
