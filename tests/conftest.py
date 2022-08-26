from datetime import datetime
from typing import Any, Callable, Coroutine, Dict, Generator, Tuple

import pytest
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy_utils import create_database, database_exists

from app.config import dev_conn_string
from app.crud.users import user
from app.db.meta import BaseModel
from app.deps import get_db
from app.main import app

dev_engine = create_engine(dev_conn_string, pool_pre_ping=True)
DevSession = sessionmaker(autoflush=False, bind=dev_engine)
if not database_exists(dev_conn_string):
    create_database(dev_conn_string)
    
BaseModel.metadata.create_all(bind=dev_engine)


def get_dev_db() -> Generator[Session, None, None]:
    try:
        s = DevSession()
        yield s
    finally:
        s.close()
        
app.dependency_overrides[get_db] = get_dev_db


@pytest.fixture()
def db():
    s = DevSession()
    yield s
    s.close()
    
    
@pytest.fixture()
def reg_data():
    return {
        "username": "Rob.Pike",
        "email": "robpike@gmail.com",
        "password": "Validpass#1",
        "password2": "Validpass#1"
    }


@pytest.fixture(autouse=True)
def clean_up() -> Generator[None, None, None]:
    yield
    s = DevSession()
    user.purge(s)
    s.close()

    
# @pytest.fixture()
# def fake_user() -> Generator[Callable[[bool], Coroutine[Any, Any, Tuple[User, str]]], None, None]:
#     yield create_fake_user
#     db.flush()


@pytest.fixture()
def client():
    return AsyncClient(app=app, base_url="http://test")


# ### UTILS ###
# def jwt_auth_headers(token: str) -> Dict[str, str]:
#     return {"Authorization": f"Bearer {token}"}


# def admin_key_auth_headers(admin_key: str) -> Dict[str, str]:
#     return {"Authorization": f"Token {admin_key}"}


# async def create_fake_user(admin: bool = False) -> Tuple[User ,str]:
#     timestamp = datetime.utcnow().timestamp()
#     name = f"Rob{timestamp}"
#     email = f"rob{timestamp}@gmail.com"
#     pwd = f"!Pass{timestamp}"
#     u = User(username=name, email=email, 
#              password=pwd, admin=admin)
#     await db.add_user_obj(u)  # type: ignore
#     return u, pwd
