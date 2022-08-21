import pytest

from app.routers.auth import INVALID_CREDS


LOGIN_URL = "/token"


def test_auth_fails_if_no_or_wrong_form(client, fake_user):
    usr, usr_pass = fake_user()
    
    no_form_data = client.post(LOGIN_URL, data={})
    assert no_form_data.status_code == 422
    
    wrong_keys_in_form_data = client.post(LOGIN_URL, data={"name":usr.username, "pass": usr_pass})
    assert wrong_keys_in_form_data.status_code == 422
    
    right_keys_wrong_type = client.post(LOGIN_URL, json={"username":usr.username, usr_pass:"password"})
    with pytest.raises(AssertionError):
        assert right_keys_wrong_type.status_code == 201   


def test_auth_fails_when_no_such_user(client):
    r = client.post(LOGIN_URL, data={"username":"Rob.Pike", "password": "1YetNotRegistered!"})
    assert r.status_code == 401
    assert r.json()["detail"] == INVALID_CREDS


def test_jwt_returned_when_creds_ok(client, fake_user):
    usr, usr_pass = fake_user()
    r = client.post(LOGIN_URL, data={"username":usr.username, "password": usr_pass})
    assert r.status_code == 201
    assert isinstance(r.json()["access_token"], str)
