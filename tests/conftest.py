from datetime import datetime
from typing import Any, Callable, Dict, Generator, Tuple

import pytest
from fastapi import Response
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy_utils import create_database, database_exists

from app.config import dev_conn_string
from app.crud.users import user
from app.db.meta import BaseModel
from app.deps import get_db
from app.main import app
from app.models.users import User
from app.schemas.users import UserInfoIn


def prepare_dev_db(conn: str) -> sessionmaker:
    if not database_exists(conn):
        create_database(conn)
        
    dev_engine = create_engine(conn, pool_pre_ping=True)
    BaseModel.metadata.create_all(bind=dev_engine)

    return sessionmaker(autoflush=False, bind=dev_engine)


DevSession = prepare_dev_db(dev_conn_string)


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
    with DevSession() as s:
        user.purge(s)


    
@pytest.fixture()
def fake_user() -> Generator[Callable[[bool], Tuple[User, str]], None, None]:
    yield create_fake_user


@pytest.fixture()
def client():
    return AsyncClient(app=app, base_url="http://test")


def login_data(name: str, _pass: str, scope: str = "users:rw") -> Dict[str, str]:
    return {"username":name, "password": _pass, "scope": scope}
    
    
def jwt_auth_headers(resp: Response) -> Dict[str, str]:
    return {'Authorization': f'Bearer {resp.json()["access_token"]}'}  # type: ignore


def admin_key_auth_headers(admin_key: str) -> Dict[str, str]:
    return {"Authorization": f"Token {admin_key}"}


def err(resp: Response) -> Any:
    return resp.json()["detail"]  # type: ignore


def create_fake_user(admin: bool = False) -> Tuple[User ,str]:
    timestamp = datetime.utcnow().timestamp()
    pwd = "!ValidPass2022"
    reg_details = UserInfoIn(
        username= f"Rob{timestamp}",
        email=f"rob{timestamp}@gmail.com",
        admin=admin,
        password=pwd,
        password2=pwd,
    )
    
    with DevSession() as s:
        u = user.create(s, reg_details)
        return u, pwd  
    