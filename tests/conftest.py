import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.mem import db


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
def client():
    return TestClient(app)
