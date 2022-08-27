from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Security
from pydantic import UUID4
from sqlalchemy.orm import Session

from app import deps
from app.crud.users import user
from app.routers.auth import USER_INACTIVE
from app.schemas.users import UserInfoIn, UserInfoOut, UserInfoUpd

CONFLICT       = "User with provided username or email already exists."
CONFLICT_NAME  = "Username already exists."
CONFLICT_EMAIL = "Email already exists."
USER_NOT_FOUND = "User not found."

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
        401: {"description": deps.INVALID_TOKEN},
        403: {"description": deps.NO_PERMISSIONS},   
    }
)

detailed_opers = APIRouter(
    dependencies=[Security(deps.has_perms_or_403, scopes=["users:rw"])],
    responses={
        404: {"description": USER_NOT_FOUND}
    }
)


@non_jwt_opers.post(path="/", status_code=201, response_model=UserInfoOut, 
                    responses={409: {"description": CONFLICT}, 401: {"description": deps.INV_ADMIN_TKN}})
async def add_user(u: UserInfoIn, authorization: str = Header(default=""), db: Session = Depends(deps.get_db)):
    if u.admin:
        await deps.check_admin_tkn(authorization)

    if not user.name_uniq(db, u.username):
        raise HTTPException(409, CONFLICT_NAME)
    
    if not user.email_uniq(db, u.email):
        raise HTTPException(409, CONFLICT_EMAIL)
    
    return user.create(db, u)
 
   
@jwt_bound_opers.get(path="/", response_model=List[Optional[UserInfoOut]], dependencies=[Depends(deps.is_admin_or_403)])
async def list_users(skip: int = 0, limit: int =100, db: Session = Depends(deps.get_db)):
    return user.get_many(db, skip, limit)


@detailed_opers.get(path="/{id}", response_model=UserInfoOut)
async def get_user(id: UUID4, db: Session = Depends(deps.get_db)):
    u = user.get(db, id)
    if not u:
        raise HTTPException(404, USER_NOT_FOUND)
    return u
    

@detailed_opers.put(path="/{id}", status_code=204, responses={409: {"description": CONFLICT}})
async def update_user(id: UUID4, upd_info: UserInfoUpd, db: Session = Depends(deps.get_db)):
    user_to_upd = user.get(db, id)
    if not user_to_upd:
        raise HTTPException(404, USER_NOT_FOUND)
    
    if upd_info.username and not user.name_uniq(db, upd_info.username, id):
        raise HTTPException(409, CONFLICT_NAME)
    
    if upd_info.email and not user.email_uniq(db, upd_info.email, id):
        raise HTTPException(409, CONFLICT_EMAIL)
    
    user.update(db, user_to_upd, upd_info)


@detailed_opers.delete(path="/{id}", status_code=204)
async def delete_user(id: UUID4, db: Session = Depends(deps.get_db)):
    usr = user.get(db, id)
    if not usr:
        raise HTTPException(404, USER_NOT_FOUND)
    user.delete(db, usr)


jwt_bound_opers.include_router(detailed_opers)
router.include_router(jwt_bound_opers)
router.include_router(non_jwt_opers)
