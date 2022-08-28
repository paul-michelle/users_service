from app.crud.users import user
from app.routers.auth import INVALID_CREDS, USER_INACTIVE
from tests.conftest import err

LOGIN_URL = "/token"


async def test_auth_fails_if_no_or_wrong_form(client, fake_user):
    usr, usr_pass = fake_user()
    
    async with client:
        no_form_data = await client.post(LOGIN_URL, data={})
        assert no_form_data.status_code == 422
        
        wrong_keys_in_form_data = await client.post(LOGIN_URL, data={"name":usr.username, "pass": usr_pass})
        assert wrong_keys_in_form_data.status_code == 422
        
        right_keys_wrong_type = await client.post(LOGIN_URL, json={"username":usr.username, usr_pass:"password"})
        assert right_keys_wrong_type.status_code == 422   


async def test_auth_fails_when_no_such_user(client):
    async with client:
        r = await client.post(LOGIN_URL, data={"username":"Rob.Pike", "password": "1YetNotRegistered!"})
        assert r.status_code == 401
        assert err(r) == INVALID_CREDS


async def test_auth_fails_when_user_not_active(client, fake_user, db):
    usr, usr_pass = fake_user()
    
    user.deactivate(db, usr)
    
    async with client:
        r = await client.post(LOGIN_URL, data={"username":usr.username, "password": usr_pass})
        assert r.status_code == 400
        assert err(r) == USER_INACTIVE


async def test_jwt_returned_when_creds_ok(client, fake_user):
    usr, usr_pass = fake_user()
    
    async with client:
        r = await client.post(
            LOGIN_URL, data={"username":usr.username, "password": usr_pass, "scope": "willberequired"}
        )
        assert r.status_code == 201
        assert isinstance(r.json()["access_token"], str)
