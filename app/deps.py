from typing import Generator
from uuid import UUID

from fastapi import Depends, HTTPException, Path
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt  # type: ignore
from pydantic import UUID4
from sqlalchemy.orm import Session

from app.config import settings
from app.crud.users import user
from app.db.session import Session
from app.models.users import User
from app.routers.auth import ALGORITHM, USER_INACTIVE

NO_PERMISSIONS = "Not authorized to perform this operation."
INVALID_TOKEN  = "Could not validate credentials."
INV_ADMIN_TKN  = "Could not validate admin credentials."

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')


def get_db() -> Generator[Session, None, None]:
    try:
        s = Session()
        yield s
    finally:
        s.close()
        
    
async def get_user_or_401(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        claims = jwt.decode(token, settings.secret_key, [ALGORITHM])
        id_string = claims["sub"]
        _id = UUID(id_string)
    except (JWTError, KeyError, ValueError) as exc:
        raise HTTPException(401, INVALID_TOKEN, {"WWW-Authenticate": "Bearer"}) from exc
    
    u = user.get(db, _id)
    if not u:
        raise HTTPException(401, INVALID_TOKEN, {"WWW-Authenticate": "Bearer"})
    return u
    
    
async def get_active_user_or_400(u: User = Depends(get_user_or_401)) -> User:
    if not u.active:
        raise HTTPException(400, USER_INACTIVE)
    return u


async def has_perms_or_403(id: UUID4 = Path(), u: User = Depends(get_active_user_or_400)) -> None:
    is_object_owner_or_admin = u.id == id or user.admin
    if not is_object_owner_or_admin:
        raise HTTPException(403, NO_PERMISSIONS)


async def is_admin_or_403(u: User = Depends(get_active_user_or_400)) -> None:
    if not u.admin:
        raise HTTPException(403, NO_PERMISSIONS)
    

async def check_admin_tkn(auth_header_value: str):   
    apart = auth_header_value.split(" ")
    if len(apart) != 2 or apart[0].capitalize() != 'Token' or apart[1] != settings.admin_key:
        raise HTTPException(401, INV_ADMIN_TKN, {"WWW-Authenticate": "Token"})
