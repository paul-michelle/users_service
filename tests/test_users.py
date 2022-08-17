from uuid import UUID

import pytest
from app.db.mem import db
from tests.utils import Resp, fake_user, auth_headers


URL                       = "/users/"
LOGIN_URL                 = "/token"
EXPECTED_USER_DETAILS_OUT = ("username", "email", "udi", "created_at", "updated_at")
VALIDATION_ERROR_MSGs     = {"6-20 chars: alphanumeric and dots.", "value is not a valid email address", 
                             "Passwords should match."}


def test_user_created_and_ok_and_pass_not_sent_back(client, reg_data):
    with Resp(client.post(URL, json=reg_data)) as r:
        assert r["status"] == 201
        for key in EXPECTED_USER_DETAILS_OUT:
            assert key in r
        
        with pytest.raises(AssertionError):
            assert "password" in r
    
    u = db.fetch_user(UUID(r["udi"]))
    assert u.username == reg_data["username"]
    assert u.email == reg_data["email"]
    assert u.password != reg_data["password"]


def test_usr_registration_fails_if_payload_invalid(client):
    invalid_reg_details = {
        "username": "~Rob~",
        "email": "robpike#gmail.com",
        "password": "Somevalidpass#1",
        "password2": "Somevalidpass#2"
    }
    with Resp(client.post(URL, json=invalid_reg_details)) as r:
        assert r["status"] == 422
        assert set(err["msg"] for err in r["detail"]).issuperset(VALIDATION_ERROR_MSGs)
        

def test_strong_pass_expected(client, reg_data):
    reg_data["password"] = "weakpass"
    reg_data["password2"] = "weakpass"
    with Resp(client.post(URL, json=reg_data)) as r:
        assert r["status"] == 422

    reg_data["password"] = "1notThatweakpass!"
    reg_data["password2"] = "1notThatweakpass!"
    with Resp(client.post(URL, json=reg_data)) as r:
        assert r["status"] == 201


def test_reg_fails_if_same_username_or_email(client, reg_data):
    client.post(URL, json=reg_data)
    with Resp(client.post(URL, json=reg_data)) as r:
        assert r["status"] == 409
        
    reg_data["username"] = "RobertButEmailSame"
    with Resp(client.post(URL, json=reg_data)) as r:
        assert r["status"] == 409
        
    reg_data["email"] = "robert@anotheremail.com"
    with Resp(client.post(URL, json=reg_data)) as r:
        assert r["status"] == 201


def test_unauthenticated_user_cannot_get_user_details(client):
    with Resp(client.get(URL)) as r:
        assert r["status"] == 401


def test_authed_usr_can_get_only_own_details(client):
    usr1, usr1pass = fake_user()
    usr2, usr2pass = fake_user()

    with Resp(client.post(LOGIN_URL, data={"username":usr1.username, "password": usr1pass})) as login_usr1:
        usr1headers = auth_headers(login_usr1["access_token"])
        # user1 trying to get details of user2:
        with Resp(client.get(f"{URL}{usr2.udi}", headers=usr1headers)) as r:
            assert r["status"] == 403
        # user1 can fetch their own deatails:
        with Resp(client.get(f"{URL}{usr1.udi}", headers=usr1headers)) as r:
            assert r["status"] == 200    

    with Resp(client.post(LOGIN_URL, data={"username":usr2.username, "password": usr2pass})) as login_usr2:
        usr2headers = auth_headers(login_usr2["access_token"])
        # vice versa, user2 trying to get details of user1:
        with Resp(client.get(f"{URL}{usr1.udi}", headers=usr2headers)) as r:
            assert r["status"] == 403   
        # user2 can fetch their own deatails: 
        with Resp(client.get(f"{URL}{usr2.udi}", headers=usr2headers)) as r:
            assert r["status"] == 200
