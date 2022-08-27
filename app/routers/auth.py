from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt  # type: ignore
from sqlalchemy.orm import Session

from app.config import settings
from app.crud.users import user
from app.deps import get_db

INVALID_CREDS      = "Invalid username or password."
USER_INACTIVE      = "User inactive."
TOKEN_EXP_MINS     = 30
COMMON_USER_SCOPES = ("users:rw", "users:r")


router = APIRouter(tags=["auth"])


@dataclass
class Token:
    access_token: str
    token_type:   str = "bearer"


def gen_access_token_str(payload: Dict[str, Any], expires_in: int = TOKEN_EXP_MINS) -> str:
    claims = deepcopy(payload)
    claims.update({"exp": datetime.utcnow() + timedelta(minutes=expires_in)})
    return jwt.encode(claims, settings.secret_key, settings.algo)


@router.post("/token", status_code=201, response_model=Token, 
             responses={401: {"description": INVALID_CREDS}, 400: {"description": USER_INACTIVE}})
async def log_in(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    u_found = user.get(db, username=form_data.username)   
    
    if not u_found or not u_found.check_password(form_data.password):
        raise HTTPException(401, INVALID_CREDS, {"WWW-Authenticate": "Bearer"})
    
    if not u_found.active:
        raise HTTPException(400, USER_INACTIVE)

    if u_found.admin:
        return Token(access_token=gen_access_token_str({"sub": str(u_found.id), "scopes": form_data.scopes}))
    
    verified_scopes = [i for i in form_data.scopes if i in COMMON_USER_SCOPES]           
    return Token(access_token=gen_access_token_str({"sub": str(u_found.id), "scopes": verified_scopes}))
