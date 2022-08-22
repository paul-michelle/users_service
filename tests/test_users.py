from uuid import UUID

import pytest

from app.config import settings
from app.db.mem import db
from app.dependencies import INV_ADMIN_TKN, NO_PERMISSIONS, INVALID_TOKEN
from app.routers.auth import USER_INACTIVE
from tests.conftest import jwt_auth_headers, admin_key_auth_headers


USERS_URL                 = "/users/"
LOGIN_URL                 = "/token"
EXPECTED_USER_DETAILS_OUT = ("username", "email", "udi", "created_at", "updated_at")
VALIDATION_ERROR_MSGs     = {"6-20 chars: alphanumeric and dots.", "value is not a valid email address", 
                             "Passwords should match."}
BEARER_NOT_PROVIDED       = "Not authenticated"


### REGISTER COMMON USER ###
async def test_usr_registration_fails_if_payload_invalid(client):
    invalid_reg_details = {
        "username": "~Rob~",
        "email": "robpike#gmail.com",
        "password": "Somevalidpass#1",
        "password2": "Somevalidpass#2"
    }
    async with client:
        r = await client.post(USERS_URL, json=invalid_reg_details)
    assert r.status_code == 422
    assert set(err["msg"] for err in r.json()["detail"]).issuperset(VALIDATION_ERROR_MSGs)
        

async def test_strong_pass_expected(client, reg_data):
    async with client:
        reg_data["password"]  = "weakpass"
        reg_data["password2"] = "weakpass"
        resp = await client.post(USERS_URL, json=reg_data)
        assert resp.status_code == 422

        reg_data["password"]  = "1notThatweakpass!"
        reg_data["password2"] = "1notThatweakpass!"
        resp = await client.post(USERS_URL, json=reg_data)
        assert resp.status_code == 201


async def test_reg_fails_if_same_username_or_email(client, reg_data):
    async with client:
        await client.post(USERS_URL, json=reg_data)
        repeated = await client.post(USERS_URL, json=reg_data)
        assert repeated.status_code == 409
        
        reg_data["username"] = "RobertButEmailSame" 
        resp = await client.post(USERS_URL, json=reg_data)
        assert resp.status_code == 409
        

async def test_user_created_and_ok_and_pass_not_sent_back(client, reg_data):
    async with client:
        resp = await client.post(USERS_URL, json=reg_data)
        assert resp.status_code == 201
    
    data_returned = resp.json()
    for key in EXPECTED_USER_DETAILS_OUT:
        assert key in data_returned
        
    with pytest.raises(AssertionError):
        assert "password" in data_returned
    
    u = await db.find_user_by_udi(UUID(data_returned["udi"]))
    assert u.username == reg_data["username"]
    assert u.email == reg_data["email"]
    assert u.password != reg_data["password"]
    assert not u.admin


### REGISTER ADMIN USER ###
async def test_admin_usr_reg_fails_if_no_or_invalid_key(client, reg_data):
    async with client:
        reg_data.update({"admin": True})

        no_auth_headers = {}
        r = await client.post(USERS_URL, json=reg_data, headers=no_auth_headers)
        assert r.status_code == 401
        assert r.json()["detail"] == INV_ADMIN_TKN
    
        empty_auth_headers = {"Authorization": ""}
        r = await client.post(USERS_URL, json=reg_data, headers=empty_auth_headers)
        assert r.json()["detail"] == INV_ADMIN_TKN
    
        wrong_tkn_type_auth_headers = {"Authorization": f"Bearer {settings.admin_key}"}
        r = await client.post(USERS_URL, json=reg_data, headers=wrong_tkn_type_auth_headers)
        assert r.json()["detail"] == INV_ADMIN_TKN

        invalid_tkn = {"Authorization": f"Token {settings.admin_key[1:]}"}
        r = await client.post(USERS_URL, json=reg_data, headers=invalid_tkn)
        assert r.json()["detail"] == INV_ADMIN_TKN


async def test_admin_usr_created_ok_if_valid_key(client, reg_data):
    reg_data.update({"admin": True})
    async with client:
        r = await client.post(USERS_URL, json=reg_data, headers=admin_key_auth_headers(settings.admin_key))
    assert r.status_code == 201
        
    u = await db.find_user_by_udi(UUID(r.json()["udi"]))
    assert u.username == reg_data["username"]
    assert u.email == reg_data["email"]
    assert u.admin


### JWT AUTH ###
async def test_jwt_required_for_usr_opers_but_create(client, reg_data):
    async with client:
        create_one = await client.post(USERS_URL, json=reg_data)
        assert create_one.status_code == 201
        
        udi = create_one.json()["udi"]
        
        get_one = await client.get(f"{USERS_URL}{udi}")
        assert get_one.status_code == 401
        assert get_one.json()["detail"] == BEARER_NOT_PROVIDED
        
        list_all = await client.get(USERS_URL)
        assert list_all.json()["detail"] == BEARER_NOT_PROVIDED

        upd_one = await client.put(f"{USERS_URL}{udi}", json={})
        assert upd_one.json()["detail"] == BEARER_NOT_PROVIDED

        del_one = await client.delete(f"{USERS_URL}{udi}")
        assert del_one.json()["detail"] == BEARER_NOT_PROVIDED
    

async def test_invalid_tkn_jwt_errors_back(client, fake_user):
    usr, usr_pass = await fake_user()
    
    async with client:
        login = await client.post(LOGIN_URL, data={"username":usr.username, "password": usr_pass})
        jwt_tkn_string = login.json()["access_token"]
        
        r = await client.get(f"{USERS_URL}{usr.udi}", headers={"Authorization": f"Bearer {jwt_tkn_string[::-1]}"})
        assert r.status_code == 401
        assert r.json()["detail"] == INVALID_TOKEN


async def test_user_no_longer_exists_errors_back(client, fake_user):
    usr, usr_pass = await fake_user()
    
    async with client:
        login = await client.post(LOGIN_URL, data={"username":usr.username, "password": usr_pass})
    
        await db.remove_user(usr.udi)
        
        r = await client.get(f"{USERS_URL}{usr.udi}", headers=jwt_auth_headers(login.json()["access_token"]))
        assert r.status_code == 401
        assert r.json()["detail"] == INVALID_TOKEN


async def test_user_not_active_errors_back(client, fake_user):
    usr, usr_pass = await fake_user()
    
    async with client:
        login = await client.post(LOGIN_URL, data={"username":usr.username, "password": usr_pass})
        
        usr.active = False
        
        r = await client.get(f"{USERS_URL}{usr.udi}", headers=jwt_auth_headers(login.json()["access_token"]))
        assert r.status_code == 400
        assert r.json()["detail"] == USER_INACTIVE
    
    
### GET ONE USER ###
async def test_authed_usr_can_get_only_own_details(client, fake_user):
    usr1, usr1pass = await fake_user()
    usr2, usr2pass = await fake_user()

    async with client:
        login_usr1 = await client.post(LOGIN_URL, data={"username":usr1.username, "password": usr1pass})
        usr1headers = jwt_auth_headers(login_usr1.json()["access_token"])
        
        resp_to_own_details_bid =  await client.get(f"{USERS_URL}{usr1.udi}", headers=usr1headers)
        assert resp_to_own_details_bid.status_code == 200
        
        resp_to_others_details_bid = await client.get(f"{USERS_URL}{usr2.udi}", headers=usr1headers)
        assert resp_to_others_details_bid.status_code == 403

        login_usr2 = await client.post(LOGIN_URL, data={"username":usr2.username, "password": usr2pass})
        usr2headers = jwt_auth_headers(login_usr2.json()["access_token"])
        
        resp_to_own_details_bid =  await client.get(f"{USERS_URL}{usr2.udi}", headers=usr2headers)
        assert resp_to_own_details_bid.status_code == 200
        
        resp_to_others_details_bid = await client.get(f"{USERS_URL}{usr1.udi}", headers=usr2headers)
        assert resp_to_others_details_bid.status_code == 403
    

async def test_admin_can_get_everyones_details(client, fake_user):
    admin_usr, admin_pass   = await fake_user(admin=True)
    common_usr1, _          = await fake_user()
    
    async with client:
        login = await client.post(LOGIN_URL, data={"username":admin_usr.username, "password": admin_pass})
        headers = jwt_auth_headers(login.json()["access_token"])
        
        resp_to_own_details_bid = await client.get(f"{USERS_URL}{admin_usr.udi}", headers=headers)
        assert resp_to_own_details_bid.status_code == 200

        resp_to_others_details_bid = await client.get(f"{USERS_URL}{common_usr1.udi}", headers=headers)
        assert resp_to_others_details_bid.status_code == 200
        

async def test_user_not_found(client, fake_user):
    admin_usr, admin_pass = await fake_user(admin=True)
    common_usr1, _        = await fake_user()
    
    async with client:
        login = await client.post(LOGIN_URL, data={"username":admin_usr.username, "password": admin_pass})
        headers = jwt_auth_headers(login.json()["access_token"])
        
        await db.remove_user(common_usr1.udi)
        
        r = await client.get(f"{USERS_URL}{common_usr1.udi}", headers=headers)
        assert r.status_code == 404


### LIST ALL USERS ###
async def test_only_admin_can_list_all_users(client, fake_user):
    admin_usr, admin_pass = await fake_user(admin=True)
    usr, usr_pass         = await fake_user()

    async with client:
        asmin_form_data = {"username":admin_usr.username, "password": admin_pass}
        admin_login = await client.post(LOGIN_URL, data=asmin_form_data)
        headers = jwt_auth_headers(admin_login.json()["access_token"])
        resp_to_admin = await client.get(USERS_URL, headers=headers)
        assert resp_to_admin.status_code == 200
        assert isinstance(resp_to_admin.json(), list)
        assert len(resp_to_admin.json()) == 2

        common_usr_form_data = {"username":usr.username, "password": usr_pass}
        common_usr_login = await client.post(LOGIN_URL, data=common_usr_form_data)
        headers = jwt_auth_headers(common_usr_login.json()["access_token"])
        resp_to_common_usr = await client.get(USERS_URL, headers=headers)
        assert resp_to_common_usr.status_code == 403
        assert resp_to_common_usr.json()["detail"] == NO_PERMISSIONS


### UPDATE USER ###

### DELETE USER ###
