from typing import List, Optional

from databases.backends.postgres import Record as DBRecord
from fastapi import APIRouter, Depends, Header, HTTPException, Security
from pydantic import UUID4

from app import deps
from app.crud.users import user
from app.routers.auth import USER_INACTIVE
from app.schemas.users import UserInfoUpd, UsrIn, UsrOut

CONFLICT       = "User with provided username or email already exists."
USER_NOT_FOUND = "User not found."

usr_inactive  = {400: {"description": USER_INACTIVE}}
unauthed      = {401: {"description": deps.INVALID_TOKEN}}
adm_unauthed  = {401: {"description": deps.INV_ADMIN_TKN}}
usr_not_found = {404: {"description": USER_NOT_FOUND}}
conflict      = {409: {"description": CONFLICT}}

router = APIRouter()
jwt_free = APIRouter(prefix="/users", tags=["users"])
jwt_bound = APIRouter(prefix="/users", tags=["users"], responses={**usr_inactive, **unauthed, **usr_not_found})


@jwt_free.post("/", status_code=201, response_model=UsrOut, responses={**conflict, **adm_unauthed})
async def add_user(reg_data: UsrIn, auth: str = Header(default="")):
    if reg_data.admin:
        await deps.check_admin_tkn(auth)
        
    auto_assigned_attrs = await user.create(reg_data)
    if not auto_assigned_attrs:
        raise HTTPException(409, CONFLICT)
    
    return {**UsrIn.as_dict(), **auto_assigned_attrs} 
 
   
@jwt_bound.get("/", response_model=List[Optional[UsrOut]], dependencies=[Depends(deps.is_admin_or_403)])
async def list_users(skip: int = 0, limit: int =100):
    return user.get_many(skip, limit)


@jwt_bound.get("/{id}", response_model=UsrOut, dependencies=[Security(deps.has_perms_or_403, scopes=["users:rw"])])
async def get_user(id: UUID4):
    u = await user.get(id)
    if not u:
        raise HTTPException(404, USER_NOT_FOUND)
    return u
    

@jwt_bound.put("/{id}", status_code=204, responses={**conflict})
async def update_user(id: UUID4, upd_info: UserInfoUpd, u: DBRecord = Security(deps.usr_or_403, scopes=["users:rw"])):
    user_obj_to_upd = await user.get(id)
    if not user_obj_to_upd:
        raise HTTPException(404, USER_NOT_FOUND)
    
    if upd_info.password:
        # TODO: check old password and that one of user_obj_to_upd
        pass

    ok = await user.update(id, upd_info)
    if not ok:
        raise HTTPException(409, CONFLICT)


@jwt_bound.delete("/{id}", status_code=204, dependencies=[Security(deps.has_perms_or_403, scopes=["users:rw"])])
async def delete_user(id: UUID4):
    if not await user.delete(id):
        raise HTTPException(404, USER_NOT_FOUND)


router.include_router(jwt_free)
router.include_router(jwt_bound)
