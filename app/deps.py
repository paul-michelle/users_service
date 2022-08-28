from typing import Generator, List, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Path
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError, jwt  # type: ignore
from pydantic import UUID4
from pydantic import BaseModel as BaseSchema
from pydantic import ValidationError, validator
from sqlalchemy.orm import Session as OrmSession

from app.config import settings
from app.crud.users import user
from app.db.session import Session
from app.models.users import User

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


def get_db() -> Generator[OrmSession, None, None]:
    try:
        s = Session()
        yield s
    finally:
        s.close()


async def usr_or_401(scopes: SecurityScopes, tkn: str = Depends(oauth2_scheme), 
                     db: OrmSession = Depends(get_db)) -> User:
    exc_headers = {"WWW-Authenticate": "Bearer"}
    if scopes.scopes:
        exc_headers = {"WWW-Authenticate": f"Bearer scope='{scopes.scope_str}'"}
        
    try:
        claims = jwt.decode(tkn, settings.secret_key, [settings.algo])
        tkn_data = TokenData(id=claims.get("sub"), scopes=claims.get("scopes"))
    except (JWTError, ValidationError) as e:
        raise HTTPException(401, INVALID_TOKEN, exc_headers) from e

    u = user.get(db, tkn_data.id)
    if not u:
        raise HTTPException(401, INVALID_TOKEN, exc_headers)

    for scope in scopes.scopes:
        if scope not in tkn_data.scopes:
            raise HTTPException(401, LACKING_PERMS, exc_headers)
        
    return u
    
    
async def active_usr_or_400(u: User = Depends(usr_or_401)) -> User:
    if not u.active:
        raise HTTPException(400, USER_INACTIVE)
    return u


async def has_perms_or_403(id: UUID4 = Path(), u: User = Depends(active_usr_or_400)) -> None:
    is_object_owner_or_admin = u.id == id or u.admin
    if not is_object_owner_or_admin:
        raise HTTPException(403, NO_PERMISSIONS)


async def is_admin_or_403(u: User = Depends(active_usr_or_400)) -> None:
    if not u.admin:
        raise HTTPException(403, NO_PERMISSIONS)
    

async def check_admin_tkn(auth_header_value: str):   
    apart = auth_header_value.split(" ")
    if len(apart) != 2 or apart[0].capitalize() != 'Token' or apart[1] != settings.admin_key:
        raise HTTPException(401, INV_ADMIN_TKN, {"WWW-Authenticate": "Token"})
