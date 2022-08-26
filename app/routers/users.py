from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import UUID4
from sqlalchemy.orm import Session

from app.crud.users import user
from app.dependencies import (
    INV_ADMIN_TKN,
    INVALID_TOKEN,
    NO_PERMISSIONS,
    check_admin_tkn,
    get_db,
    has_perms_or_403,
    is_admin_or_403,
)
from app.routers.auth import USER_INACTIVE
from app.schemas.users import UserInfoIn, UserInfoOut, UserInfoUpd

CONFICT        = "User with provided username or email already exists."
CONFICT_NAME   = "Username already exists."
CONFICT_EMAIL  = "Email already exists."
NOT_FOUND      = "User not found."

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


@non_jwt_opers.post(path="/", status_code=201, response_model=UserInfoOut, 
                    responses={409: {"description": CONFICT}, 401: {"description": INV_ADMIN_TKN}})
async def add_user(u: UserInfoIn, authorization: str = Header(default=""), db: Session = Depends(get_db)):
    if u.admin:
        await check_admin_tkn(authorization)
    
    usr_created_obj = user.create(db, u)
    if not usr_created_obj:
        raise HTTPException(409, CONFICT)
    
    return usr_created_obj
 
   
@jwt_bound_opers.get(path="/", response_model=List[Optional[UserInfoOut]], dependencies=[Depends(is_admin_or_403)])
async def list_users(skip: int = 0, limit: int =100, db: Session = Depends(get_db)):
    return user.get_many(db, skip, limit)


@detailed_opers.get(path="/{id}", response_model=UserInfoOut)
async def get_user(id: UUID4, db: Session = Depends(get_db)):
    u = user.get(db, id)
    if not u:
        raise HTTPException(404, NOT_FOUND)
    return u
    

@detailed_opers.put(path="/{id}", status_code=204, responses={409: {"description": CONFICT}})
async def update_user(id: UUID4, upd_info: UserInfoUpd, db: Session = Depends(get_db)):
    user_to_upd = user.get(db, id)
    if not user_to_upd:
        raise HTTPException(404, NOT_FOUND)
    
    if upd_info.username and not user.name_uniq(db, upd_info.username, id):
        raise HTTPException(409, CONFICT_NAME)
    
    if upd_info.email and not user.email_uniq(db, upd_info.email, id):
        raise HTTPException(409, CONFICT_EMAIL)
    
    user.update(db, user_to_upd, upd_info)


@detailed_opers.delete(path="/{id}", status_code=204)
async def delete_user(id: UUID4, db: Session = Depends(get_db)):
    usr = user.get(db, id)
    if not usr:
        raise HTTPException(404, NOT_FOUND)
    user.delete(db, usr)


jwt_bound_opers.include_router(detailed_opers)
router.include_router(jwt_bound_opers)
router.include_router(non_jwt_opers)
