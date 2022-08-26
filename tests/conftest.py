from datetime import datetime
from typing import Any, Callable, Coroutine, Dict, Generator, Tuple

import pytest
from httpx import AsyncClient

from app.db.mem import User, db
from app.main import app


### FIXTURES ###
@pytest.fixture()
def reg_data():
    yield {
        "username": "Rob.Pike",
        "email": "robpike@gmail.com",
        "password": "Validpass#1",
        "password2": "Validpass#1"
    }
    db.flush()


@pytest.fixture()
def fake_user() -> Generator[Callable[[bool], Coroutine[Any, Any, Tuple[User, str]]], None, None]:
    yield create_fake_user
    db.flush()


@pytest.fixture()
def client():
    return AsyncClient(app=app, base_url="http://test")


### UTILS ###
def jwt_auth_headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def admin_key_auth_headers(admin_key: str) -> Dict[str, str]:
    return {"Authorization": f"Token {admin_key}"}


async def create_fake_user(admin: bool = False) -> Tuple[User ,str]:
    timestamp = datetime.utcnow().timestamp()
    name = f"Rob{timestamp}"
    email = f"rob{timestamp}@gmail.com"
    pwd = f"!Pass{timestamp}"
    u = User(username=name, email=email, 
             password=pwd, admin=admin)
    await db.add_user_obj(u)  # type: ignore
    return u, pwd
