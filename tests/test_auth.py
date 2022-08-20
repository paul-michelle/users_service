import pytest

from app.routers.auth import INVALID_CREDS
from tests.utils import Resp, fake_user


LOGIN_URL = "/token"


def test_auth_fails_if_no_or_wrong_form(client):
    usr, usr_pass = fake_user()
    
    with Resp(client.post(LOGIN_URL, data={})) as login:
        assert login["status"] == 422
     
    with Resp(client.post(LOGIN_URL, data={"name":usr.username, "pass": usr_pass})) as login:
        assert login["status"] == 422
    
    # sending correct values, but not as form-data:
    with Resp(client.post(LOGIN_URL, json={"username":usr.username, usr_pass:"password"})) as login:
        with pytest.raises(AssertionError):
            assert login["status"] == 201   


def test_auth_fails_when_no_such_user(client):
    with Resp(client.post(LOGIN_URL, data={"username":"Rob.Pike", "password": "1YetNotRegistered!"})) as login:
        assert login["status"] == 401
        assert login["detail"] == INVALID_CREDS


def test_jwt_returned_when_creds_ok(client):
    usr, usr_pass = fake_user()

    with Resp(client.post(LOGIN_URL, data={"username":usr.username, "password": usr_pass})) as login:
        assert login["status"] == 201
        assert isinstance(login["access_token"], str)
