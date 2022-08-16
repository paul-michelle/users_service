import re
from datetime import datetime
from typing import List, Optional, Dict, Any, TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, validator, UUID1

from app.db.mem import db
from app.routers.auth import (
    has_perms_or_403, 
    is_admin_or_403,
    INVALID_TOKEN, 
    USER_INACTIVE,
    NO_PERMISSIONS
)


if TYPE_CHECKING:
    from typing import Generator
    from pydantic.typing import AnyCallable
    CallableGenerator = Generator[AnyCallable, None, None]
    
    
VALID_PASS_PATTERN = re.compile(r"^(?=\S{6,20}$)(?=.*?\d)(?=.*?[a-z])(?=.*?[A-Z])(?=.*?[^A-Za-z\s0-9])")  # NOSONAR
PASS_FMT           = "6-20 chars, incl. a lower, an upper, and a special char."
USERNAME_FMT       = "Alphanumeric string expected."
PASS_MISMATCH      = "Passwords should match."
CONFICT            = "User with provided username or email already exists."
NOT_FOUND          = "User not found."


### VALIDATORS ###
class PassStr(str):
    
    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        field_schema.update(type='string', format=PASS_FMT)

    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield cls.validate

    @classmethod
    def validate(cls, value: str) -> str:
        if not VALID_PASS_PATTERN.match(value):
            raise ValueError(PASS_FMT)
        return value


class UserInfoBase(BaseModel):
    username: str
    email:    EmailStr
    
    @validator("username")
    def is_valid_name(cls, username):
        if not username.isalnum():
            raise ValueError(USERNAME_FMT)
        return username
    

class UserInfoIn(UserInfoBase):
    admin:     Optional[bool]
    password:  PassStr
    password2: str
        
    @validator("password2")
    def pass_match(cls, password2, values):
        password = values.get("password")
        if password and password2 != password:
            raise ValueError(PASS_MISMATCH)
        return password2


class UserInfoOut(UserInfoBase):
    udi:        UUID1
    created_at: datetime
    updated_at: datetime
    admin:      bool


### ROUTERS ###
router = APIRouter()

non_authed_oper = APIRouter(
    prefix="/users",
    tags=["users"]
)

authed_oper = APIRouter(
    prefix="/users", 
    tags=["users"],
    responses={
        400: {"description": USER_INACTIVE},
        401: {"description": INVALID_TOKEN},
        403: {"description": NO_PERMISSIONS},   
    }
)

detailed_oper = APIRouter(
    dependencies=[Depends(has_perms_or_403)],
    responses={
        404: {"description": NOT_FOUND}
    }
)


#### PATH OPERATIONS ###
@non_authed_oper.post(path="/", status_code=201, responses={409: {"description": CONFICT}}, response_model=UserInfoOut)
async def add_user(u: UserInfoIn):
    user_created = await db.add_user(u.username, u.email, u.password, u.admin)
    if not user_created:
        raise HTTPException(409, CONFICT)
    return user_created
 
   
@authed_oper.get(path="/", response_model=List[Optional[UserInfoOut]], dependencies=[Depends(is_admin_or_403)])
async def list_users():
    return await db.list_users()


@detailed_oper.get(path="/{udi}", response_model=UserInfoOut)
async def get_user(udi: UUID1):
    u = await db.find_user_by_udi(udi)
    if not u:
        raise HTTPException(404, NOT_FOUND)
    return u
    

@detailed_oper.put(path="/{udi}", status_code=204, responses={409: {"description": CONFICT}})
async def update_user(udi: UUID1, upd_info: UserInfoIn):
    user_to_upd = await db.find_user_by_udi(udi)
    if not user_to_upd:
        raise HTTPException(404, NOT_FOUND)
    ok = await db.upd_user(user_to_upd, upd_info.dict())
    if not ok:
        raise HTTPException(409, CONFICT)


@detailed_oper.delete(path="/{udi}", status_code=204)
async def delete_user(udi: UUID1):
    ok = await db.del_user(udi)
    if not ok:
        raise HTTPException(404, NOT_FOUND)


authed_oper.include_router(detailed_oper)
router.include_router(authed_oper)
router.include_router(non_authed_oper)
