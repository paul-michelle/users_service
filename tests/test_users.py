from uuid import UUID

import pytest
from app.db.mem import db
from app.dependencies import ADMIN_KEY, INV_ADMIN_TKN, NO_PERMISSIONS, INVALID_TOKEN
from app.routers.auth import USER_INACTIVE
from tests.conftest import jwt_auth_headers, admin_key_auth_headers


USERS_URL                 = "/users/"
LOGIN_URL                 = "/token"
EXPECTED_USER_DETAILS_OUT = ("username", "email", "udi", "created_at", "updated_at")
VALIDATION_ERROR_MSGs     = {"6-20 chars: alphanumeric and dots.", "value is not a valid email address", 
                             "Passwords should match."}
BEARER_NOT_PROVIDED       = "Not authenticated"


### REGISTER COMMON USER ###
def test_usr_registration_fails_if_payload_invalid(client):
    invalid_reg_details = {
        "username": "~Rob~",
        "email": "robpike#gmail.com",
        "password": "Somevalidpass#1",
        "password2": "Somevalidpass#2"
    }
    r = client.post(USERS_URL, json=invalid_reg_details)
    assert r.status_code == 422
    assert set(err["msg"] for err in r.json()["detail"]).issuperset(VALIDATION_ERROR_MSGs)
        

def test_strong_pass_expected(client, reg_data):
    reg_data["password"]  = "weakpass"
    reg_data["password2"] = "weakpass"
    assert client.post(USERS_URL, json=reg_data).status_code == 422

    reg_data["password"]  = "1notThatweakpass!"
    reg_data["password2"] = "1notThatweakpass!"
    assert client.post(USERS_URL, json=reg_data).status_code == 201


def test_reg_fails_if_same_username_or_email(client, reg_data):
    client.post(USERS_URL, json=reg_data)
    repeated = client.post(USERS_URL, json=reg_data)
    assert repeated.status_code == 409
        
    reg_data["username"] = "RobertButEmailSame"
    assert client.post(USERS_URL, json=reg_data).status_code == 409
        
    reg_data["email"] = "robert@anotheremail.com"
    assert client.post(USERS_URL, json=reg_data).status_code == 201


def test_user_created_and_ok_and_pass_not_sent_back(client, reg_data):
    r = client.post(USERS_URL, json=reg_data)
    assert r.status_code == 201
    
    data_returned = r.json()
    for key in EXPECTED_USER_DETAILS_OUT:
        assert key in data_returned
        
    with pytest.raises(AssertionError):
        assert "password" in data_returned
    
    u = db.fetch_user(UUID(data_returned["udi"]))
    assert u.username == reg_data["username"]
    assert u.email == reg_data["email"]
    assert u.password != reg_data["password"]
    assert not u.admin


### REGISTER ADMIN USER ###
def test_admin_usr_reg_fails_if_no_or_invalid_key(client, reg_data):
    reg_data.update({"admin": True})

    no_auth_headers = {}
    r = client.post(USERS_URL, json=reg_data, headers=no_auth_headers)
    assert r.status_code == 401
    assert r.json()["detail"] == INV_ADMIN_TKN
    
    empty_auth_headers = {"Authorization": ""}
    r = client.post(USERS_URL, json=reg_data, headers=empty_auth_headers)
    assert r.json()["detail"] == INV_ADMIN_TKN
    
    wrong_tkn_type_auth_headers = {"Authorization": f"Bearer {ADMIN_KEY}"}
    r = client.post(USERS_URL, json=reg_data, headers=wrong_tkn_type_auth_headers)
    assert r.json()["detail"] == INV_ADMIN_TKN

    invalid_tkn = {"Authorization": f"Token {ADMIN_KEY[1:]}"}
    r = client.post(USERS_URL, json=reg_data, headers=invalid_tkn)
    assert r.json()["detail"] == INV_ADMIN_TKN


def test_admin_usr_created_ok_if_valid_key(client, reg_data):
    reg_data.update({"admin": True})
    
    r = client.post(USERS_URL, json=reg_data, headers=admin_key_auth_headers(ADMIN_KEY))
    assert r.status_code == 201
        
    u = db.fetch_user(UUID(r.json()["udi"]))
    assert u.username == reg_data["username"]
    assert u.email == reg_data["email"]
    assert u.admin


### JWT AUTH ###
def test_jwt_required_for_usr_opers_but_create(client, reg_data):
    create_one = client.post(USERS_URL, json=reg_data)
    assert create_one.status_code == 201
    
    udi = create_one.json()["udi"]
    
    get_one = client.get(f"{USERS_URL}{udi}")
    assert get_one.status_code == 401
    assert get_one.json()["detail"] == BEARER_NOT_PROVIDED
    
    list_all = client.get(USERS_URL)
    assert list_all.json()["detail"] == BEARER_NOT_PROVIDED

    upd_one = client.put(f"{USERS_URL}{udi}", json={})
    assert upd_one.json()["detail"] == BEARER_NOT_PROVIDED

    del_one = client.delete(f"{USERS_URL}{udi}")
    assert del_one.json()["detail"] == BEARER_NOT_PROVIDED
    

def test_invalid_tkn_jwt_errors_back(client, fake_user):
    usr, usr_pass = fake_user()

    login = client.post(LOGIN_URL, data={"username":usr.username, "password": usr_pass})
    jwt_tkn_string = login.json()["access_token"]
    r = client.get(f"{USERS_URL}{usr.udi}", headers={"Authorization": f"Bearer {jwt_tkn_string[::-1]}"})
    assert r.status_code == 401
    assert r.json()["detail"] == INVALID_TOKEN


def test_user_no_longer_exists_errors_back(client, fake_user):
    usr, usr_pass = fake_user()
    
    login = client.post(LOGIN_URL, data={"username":usr.username, "password": usr_pass})
    
    db.remove_user(usr.udi)
    
    r = client.get(f"{USERS_URL}{usr.udi}", headers=jwt_auth_headers(login.json()["access_token"]))
    assert r.status_code == 401
    assert r.json()["detail"] == INVALID_TOKEN
    

def test_user_not_active_errors_back(client, fake_user):
    usr, usr_pass = fake_user()
    
    login = client.post(LOGIN_URL, data={"username":usr.username, "password": usr_pass})
    
    usr.active = False
    
    r = client.get(f"{USERS_URL}{usr.udi}", headers=jwt_auth_headers(login.json()["access_token"]))
    assert r.status_code == 400
    assert r.json()["detail"] == USER_INACTIVE
    
    
### GET ONE USER ###
def test_authed_usr_can_get_only_own_details(client, fake_user):
    usr1, usr1pass = fake_user()
    usr2, usr2pass = fake_user()

    login_usr1 = client.post(LOGIN_URL, data={"username":usr1.username, "password": usr1pass})
    usr1headers = jwt_auth_headers(login_usr1.json()["access_token"])
    assert client.get(f"{USERS_URL}{usr1.udi}", headers=usr1headers).status_code == 200
    assert client.get(f"{USERS_URL}{usr2.udi}", headers=usr1headers).status_code == 403

    login_usr2 = client.post(LOGIN_URL, data={"username":usr2.username, "password": usr2pass})
    usr2headers = jwt_auth_headers(login_usr2.json()["access_token"])
    assert client.get(f"{USERS_URL}{usr1.udi}", headers=usr2headers).status_code == 403
    assert client.get(f"{USERS_URL}{usr2.udi}", headers=usr2headers).status_code == 200
    

def test_admin_can_get_everyones_details(client, fake_user):
    admin_usr, admin_pass   = fake_user(admin=True)
    common_usr1, _          = fake_user()
    commin_usr2, _          = fake_user()
    
    login = client.post(LOGIN_URL, data={"username":admin_usr.username, "password": admin_pass})
    headers = jwt_auth_headers(login.json()["access_token"])
    assert client.get(f"{USERS_URL}{common_usr1.udi}", headers=headers).status_code == 200
    assert client.get(f"{USERS_URL}{commin_usr2.udi}", headers=headers).status_code == 200
    assert client.get(f"{USERS_URL}{admin_usr.udi}", headers=headers).status_code == 200


def test_user_not_found(client, fake_user):
    admin_usr, admin_pass = fake_user(admin=True)
    common_usr1, _        = fake_user()
    
    login = client.post(LOGIN_URL, data={"username":admin_usr.username, "password": admin_pass})
    headers = jwt_auth_headers(login.json()["access_token"])
    
    db.remove_user(common_usr1.udi)
    
    assert client.get(f"{USERS_URL}{common_usr1.udi}", headers=headers).status_code == 404


### LIST ALL USERS ###
def test_only_admin_can_list_all_users(client, fake_user):
    admin_usr, admin_pass = fake_user(admin=True)
    usr, usr_pass         = fake_user()

    admin_login =client.post(LOGIN_URL, data={"username":admin_usr.username, "password": admin_pass})
    headers = jwt_auth_headers(admin_login.json()["access_token"])
    resp_to_admin = client.get(USERS_URL, headers=headers)
    assert resp_to_admin.status_code == 200
    assert isinstance(resp_to_admin.json(), list)
    assert len(resp_to_admin.json()) == 2

    common_usr_login = client.post(LOGIN_URL, data={"username":usr.username, "password": usr_pass})
    headers = jwt_auth_headers(common_usr_login.json()["access_token"])
    resp_to_common_usr= client.get(USERS_URL, headers=headers)
    assert resp_to_common_usr.status_code == 403
    assert resp_to_common_usr.json()["detail"] == NO_PERMISSIONS


### UPDATE USER ###

### DELETE USER ###
