import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Any
from copy import deepcopy

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt  # type: ignore

from app.db.mem import db

load_dotenv()

INVALID_CREDS  = "Invalid username or password."
ALGORITHM      = "HS256"
SECRET_KEY     = os.environ.get("SECRET_KEY")
TOKEN_EXP_MINS = 30


router = APIRouter(tags=["auth"])


@dataclass
class Token:
    access_token: str
    token_type:   str = "bearer"


def create_access_token_string(payload: Dict[str, Any], expires_in: int = TOKEN_EXP_MINS) -> str:
    claims = deepcopy(payload)
    claims.update({"exp": datetime.utcnow() + timedelta(minutes=expires_in)})
    return jwt.encode(claims, SECRET_KEY, ALGORITHM)


@router.post("/token", status_code=201, response_model=Token, responses={400: {"description": INVALID_CREDS}})
async def log_in(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db.find_user_by_creds(form_data.username, form_data.password)   
    if not user:
        raise HTTPException(401, INVALID_CREDS, {"WWW-Authenticate": "Bearer"})
    return Token(access_token=create_access_token_string({"udi": str(user.udi)}))
