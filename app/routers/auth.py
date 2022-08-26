from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt  # type: ignore

from app.config import settings

INVALID_CREDS  = "Invalid username or password."
USER_INACTIVE  = "User inactive."
ALGORITHM      = "HS256"
TOKEN_EXP_MINS = 30


router = APIRouter(tags=["auth"])


@dataclass
class Token:
    access_token: str
    token_type:   str = "bearer"


def create_access_token_string(payload: Dict[str, Any], expires_in: int = TOKEN_EXP_MINS) -> str:
    claims = deepcopy(payload)
    claims.update({"exp": datetime.utcnow() + timedelta(minutes=expires_in)})
    return jwt.encode(claims, settings.secret_key, ALGORITHM)


@router.post("/token", status_code=201, response_model=Token, 
             responses={401: {"description": INVALID_CREDS}, 400: {"description": USER_INACTIVE}})
async def log_in(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db.find_user_by_creds(form_data.username, form_data.password)   
    if not user:
        raise HTTPException(401, INVALID_CREDS, {"WWW-Authenticate": "Bearer"})
    if not user.active:
        raise HTTPException(400, USER_INACTIVE)
    return Token(access_token=create_access_token_string({"sub": str(user.id)}))
