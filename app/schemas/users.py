import re
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

from pydantic import UUID4
from pydantic import BaseModel as BaseSchema
from pydantic import EmailStr, validator

if TYPE_CHECKING:  # pragma: no cover
    from typing import Generator

    from pydantic.typing import AnyCallable
    CallableGenerator = Generator[AnyCallable, None, None]

NAME_MAX_LENGTH = 20
PASS_PATTERN    = re.compile(r"^(?=\S{6,20}$)(?=.*?\d)(?=.*?[a-z])(?=.*?[A-Z])(?=.*?[^A-Za-z\s0-9])")  # NOSONAR
NAME_PATTERN    = re.compile(r"^[a-z\d.]{6,20}$", flags=re.I)
PASS_FMT        = "6-20 chars, incl. a lower, an upper, and a special char."
USERNAME_FMT    = "6-20 chars: alphanumeric and dots."
PASS_MISMATCH   = "Passwords should match."
OLD_PASS_NEEDED = "Old password not provided."


class PassStr(str):
    
    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:  # pragma: no cover
        field_schema.update(type='string', format=PASS_FMT)

    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield cls.validate

    @classmethod
    def validate(cls, value: str) -> str:
        if not PASS_PATTERN.match(value):
            raise ValueError(PASS_FMT)
        return value


class NameStr(str):
    
    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:  # pragma: no cover
        field_schema.update(type='string', format=USERNAME_FMT)

    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield cls.validate

    @classmethod
    def validate(cls, value: str) -> str:
        if not NAME_PATTERN.match(value):
            raise ValueError(USERNAME_FMT)
        return value
    
    
class UserInfoBase(BaseSchema):
    username: NameStr
    email:    EmailStr
    

class UserInfoIn(UserInfoBase):
    admin:     Optional[bool]
    password:  PassStr
    password2: str
        
    @validator("password2")
    def pass_match(cls, password2, values):
        password = values.get("password")
        if password and password2 != password:
            raise ValueError(PASS_MISMATCH)
        return password2


class UserInfoUpd(BaseSchema):
    username:  Optional[NameStr]  = None
    email:     Optional[EmailStr] = None
    oldpass:   Optional[PassStr]  = None
    password:  Optional[PassStr]  = None
    password2: Optional[str]      = None
        
    @validator("password2")
    def pass_match_if_new(cls, password2, values):
        password = values.get("password")
        old_pass = values.get("oldpass")
        
        if password and not old_pass:
             raise ValueError(OLD_PASS_NEEDED)
        
        if password and password2 != password:
            raise ValueError(PASS_MISMATCH)
        
        return password2


class UserInfoOut(UserInfoBase):
    id :        UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class UserDB(UserInfoOut): 
    password: str
    active:   bool
    admin:    bool
    