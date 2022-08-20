import re
from datetime import datetime
from typing import List, Optional, Dict, Any, TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, EmailStr, validator, UUID4

from app.db.mem import db
from app.dependencies import (
    has_perms_or_403, 
    is_admin_or_403,
    check_admin_tkn,
    INVALID_TOKEN, 
    INV_ADMIN_TKN,
    USER_INACTIVE,
    NO_PERMISSIONS
)


if TYPE_CHECKING:
    from typing import Generator
    from pydantic.typing import AnyCallable
    CallableGenerator = Generator[AnyCallable, None, None]
    
    
PASS_PATTERN  = re.compile(r"^(?=\S{6,20}$)(?=.*?\d)(?=.*?[a-z])(?=.*?[A-Z])(?=.*?[^A-Za-z\s0-9])")  # NOSONAR
NAME_PATTERN  = re.compile(r"^[a-z\d.]{6,20}$", flags=re.I)
PASS_FMT      = "6-20 chars, incl. a lower, an upper, and a special char."
USERNAME_FMT  = "6-20 chars: alphanumeric and dots."
PASS_MISMATCH = "Passwords should match."
CONFICT       = "User with provided username or email already exists."
NOT_FOUND     = "User not found."


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
        if not PASS_PATTERN.match(value):
            raise ValueError(PASS_FMT)
        return value


class NameStr(str):
    
    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        field_schema.update(type='string', format=USERNAME_FMT)

    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield cls.validate

    @classmethod
    def validate(cls, value: str) -> str:
        if not NAME_PATTERN.match(value):
            raise ValueError(USERNAME_FMT)
        return value
    
    
class UserInfoBase(BaseModel):
    username: NameStr
    email:    EmailStr
    

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
    udi:        UUID4
    created_at: datetime
    updated_at: datetime


### ROUTERS ###
router = APIRouter()

non_jwt_opers = APIRouter(
    prefix="/users",
    tags=["users"]
)

jwt_bound_opers = APIRouter(
    prefix="/users", 
    tags=["users"],
    responses={
        400: {"description": USER_INACTIVE},
        401: {"description": INVALID_TOKEN},
        403: {"description": NO_PERMISSIONS},   
    }
)

detailed_opers = APIRouter(
    dependencies=[Depends(has_perms_or_403)],
    responses={
        404: {"description": NOT_FOUND}
    }
)


#### PATH OPERATIONS ###
@non_jwt_opers.post(path="/", status_code=201, response_model=UserInfoOut, 
                    responses={409: {"description": CONFICT}, 401: {"description": INV_ADMIN_TKN}})
async def add_user(u: UserInfoIn, authorization: Optional[str] = Header(default=None)):
    if u.admin:
        await check_admin_tkn(authorization)
    
    user_created = await db.add_user(u.username, u.email, u.password, u.admin)
    if not user_created:
        raise HTTPException(409, CONFICT)
    return user_created
 
   
@jwt_bound_opers.get(path="/", response_model=List[Optional[UserInfoOut]], dependencies=[Depends(is_admin_or_403)])
async def list_users():
    return await db.list_users()


@detailed_opers.get(path="/{udi}", response_model=UserInfoOut)
async def get_user(udi: UUID4):
    u = await db.find_user_by_udi(udi)
    if not u:
        raise HTTPException(404, NOT_FOUND)
    return u
    

@detailed_opers.put(path="/{udi}", status_code=204, responses={409: {"description": CONFICT}})
async def update_user(udi: UUID4, upd_info: UserInfoIn):
    user_to_upd = await db.find_user_by_udi(udi)
    if not user_to_upd:
        raise HTTPException(404, NOT_FOUND)
    ok = await db.upd_user(user_to_upd, upd_info.dict())
    if not ok:
        raise HTTPException(409, CONFICT)


@detailed_opers.delete(path="/{udi}", status_code=204)
async def delete_user(udi: UUID4):
    ok = await db.del_user(udi)
    if not ok:
        raise HTTPException(404, NOT_FOUND)


jwt_bound_opers.include_router(detailed_opers)
router.include_router(jwt_bound_opers)
router.include_router(non_jwt_opers)
