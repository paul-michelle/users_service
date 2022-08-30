from typing import List, Optional
from uuid import UUID

from databases.backends.postgres import Record as DBRecord
from fastapi import Depends, HTTPException, Path
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError, jwt  # type: ignore
from pydantic import UUID4
from pydantic import BaseModel as BaseSchema
from pydantic import ValidationError, validator

from app.config import settings
from app.crud.users import user

NO_PERMISSIONS = "Not authorized to perform this operation."
INVALID_TOKEN  = "Could not validate credentials."
LACKING_PERMS  = "Operation out of permissions scope."
INV_ADMIN_TKN  = "Could not validate admin credentials."
USER_INACTIVE  = "User inactive."

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl='token', 
    scopes={"users:rw": "Read, update, delete user."}
)


class TokenData(BaseSchema):
    id     : UUID4
    scopes : List[Optional[str]] = []
    
    @validator("id", pre=True)
    def is_uuid_string(cls, _id):
        return UUID(_id)


async def usr_or_401(scopes: SecurityScopes, tkn: str = Depends(oauth2_scheme)) -> DBRecord:
    exc_headers = {"WWW-Authenticate": "Bearer"}
    if scopes.scopes:
        exc_headers = {"WWW-Authenticate": f"Bearer scope='{scopes.scope_str}'"}
        
    try:
        claims = jwt.decode(tkn, settings.secret_key, [settings.algo])
        tkn_data = TokenData(id=claims.get("sub"), scopes=claims.get("scopes"))
    except (JWTError, ValidationError) as e:
        raise HTTPException(401, INVALID_TOKEN, exc_headers) from e

    u = await user.get(tkn_data.id)
    if not u:
        raise HTTPException(401, INVALID_TOKEN, exc_headers)

    for scope in scopes.scopes:
        if scope not in tkn_data.scopes:
            raise HTTPException(401, LACKING_PERMS, exc_headers)
        
    return u
    
    
async def active_usr_or_400(u: DBRecord = Depends(usr_or_401)) -> DBRecord:
    if not u.active:
        raise HTTPException(400, USER_INACTIVE)
    return u


async def has_perms_or_403(id: UUID4 = Path(), u: DBRecord = Depends(active_usr_or_400)) -> None:
    is_obj_owner_or_admin = u.id == id or u.admin
    if not is_obj_owner_or_admin:
        raise HTTPException(403, NO_PERMISSIONS)


async def usr_or_403(id: UUID4 = Path(), u: DBRecord = Depends(active_usr_or_400)) -> DBRecord:
    is_obj_owner_or_admin = u.id == id or u.admin
    if not is_obj_owner_or_admin:
        raise HTTPException(403, NO_PERMISSIONS)  
    return u


async def is_admin_or_403(u: DBRecord = Depends(active_usr_or_400)) -> None:
    if not u.admin:
        raise HTTPException(403, NO_PERMISSIONS)
    

async def check_admin_tkn(auth_header_value: str) -> None:   
    apart = auth_header_value.split(" ")
    if len(apart) != 2 or apart[0].capitalize() != 'Token' or apart[1] != settings.admin_key:
        raise HTTPException(401, INV_ADMIN_TKN, {"WWW-Authenticate": "Token"})
