import os
import uuid
from typing import Optional

from pydantic import UUID4
from fastapi import Depends, HTTPException, Path
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError  # type: ignore
from dotenv import load_dotenv

from app.db.mem import db, User
from app.routers.auth import SECRET_KEY, ALGORITHM

load_dotenv()

USER_INACTIVE  = "User inactive."
NO_PERMISSIONS = "Not authorized to perform this operation."
INVALID_TOKEN  = "Could not validate credentials."
INV_ADMIN_TKN  = "Could not validate admin credentials."
ADMIN_KEY      = os.environ.get("ADMIN_KEY")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')


async def get_user_or_401(token: str = Depends(oauth2_scheme)) -> User:
    try:
        claims = jwt.decode(token, SECRET_KEY, [ALGORITHM])
        udi_string = claims["udi"]
        udi = uuid.UUID(udi_string)
    except (JWTError, KeyError, ValueError) as exc:
        raise HTTPException(401, INVALID_TOKEN, {"WWW-Authenticate": "Bearer"}) from exc
    
    user = await db.find_user_by_udi(udi)
    if not user:
        raise HTTPException(401, INVALID_TOKEN, {"WWW-Authenticate": "Bearer"})
    return user
    
    
async def get_active_user_or_400(user: User = Depends(get_user_or_401)):
    if not user.active:
        raise HTTPException(400, USER_INACTIVE)
    return user


async def has_perms_or_403(udi: UUID4 = Path(), user: User = Depends(get_active_user_or_400)):
    is_object_owner_or_admin = user.udi == udi or user.admin
    if not is_object_owner_or_admin:
        raise HTTPException(403, NO_PERMISSIONS)


async def is_admin_or_403(user: User = Depends(get_active_user_or_400)):
    if not user.admin:
        raise HTTPException(403, NO_PERMISSIONS)
    

async def check_admin_tkn(auth_header_value: Optional[str]):
    exc = HTTPException(401, INV_ADMIN_TKN, {"WWW-Authenticate": "Token"})
    
    if not auth_header_value:
        raise exc
    
    apart = auth_header_value.split(" ")
    if len(apart) != 2:
        raise exc
    
    if apart[0].capitalize() != 'Token' or apart[1] != ADMIN_KEY:
        raise exc
