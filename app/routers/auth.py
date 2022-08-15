import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Any
from copy import deepcopy

from dotenv import load_dotenv
from pydantic import UUID1
from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError

from app.db.mem import db, User

load_dotenv()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

INVALID_TOKEN               = "Could not validate credentials."
INVALID_CREDS               = "Invalid username or password."
USER_INACTIVE               = "User inactive."
NO_PERMISSIONS              = "Not authorized to perform this operation."

ALGORITHM                   = "HS256"
SECRET_KEY                  = os.environ.get("SECRET_KEY")
ACCESS_TOKEN_EXPIRE_MINUTES = 30

router = APIRouter(tags=["auth"])


@dataclass
class Token:
    access_token: str
    token_type:   str = "bearer"


def create_access_token(payload: Dict[str, Any], expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> Token:
    claims = deepcopy(payload)
    claims.update({"exp": datetime.utcnow() + timedelta(minutes=expires_in)})
    return jwt.encode(claims, SECRET_KEY, ALGORITHM)


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


async def has_perms_or_403(udi: UUID1 = Path(), user: User = Depends(get_active_user_or_400)):
    is_object_owner_or_admin = user.udi == udi or user.admin
    if not is_object_owner_or_admin:
        raise HTTPException(403, NO_PERMISSIONS)


async def is_admin_or_403(user: User = Depends(get_active_user_or_400)):
    if not user.admin:
        raise HTTPException(403, NO_PERMISSIONS)


@router.post("/token", status_code=201, response_model=Token, responses={400: {"description": INVALID_CREDS}})
async def log_in(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db.find_user_by_creds(form_data.username, form_data.password)   
    if not user:
        raise HTTPException(401, INVALID_CREDS, {"WWW-Authenticate": "Bearer"})
    return Token(access_token=create_access_token({"udi": str(user.udi)}))
