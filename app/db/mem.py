from uuid import uuid1
from typing import Optional, List, Dict, Any
from datetime import datetime

from pydantic import BaseModel, UUID1, validator

from app.db.utils import password_manager


class User(BaseModel):
    username:   str
    email:      str
    password:   str
    active:     bool               = True
    admin:      bool               = False
    udi:        Optional[UUID1]    = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @validator("udi", always=True)
    def generate_udi_if_null(cls, udi: Optional[UUID1]) -> UUID1:
        return udi if udi else uuid1()
    
    @validator("created_at", always=True)
    def set_created_at_default(cls, created_at: Optional[datetime]) -> datetime:
        return created_at if created_at else datetime.now()
    
    @validator("updated_at", always=True)
    def set_updated_at_default(cls, updated_at: Optional[datetime], values: Dict[str, Any]) -> datetime:
        return updated_at if updated_at else values["created_at"]
    
    @validator("password")
    def hash_password(cls, plain_password: str) -> str:
        return password_manager.hash(plain_password)
    
    def set_password(self, plain_password: str) -> None:
        self.password = password_manager.hash(plain_password)
    
    def check_password(self, plain_password: str) -> bool:
        return password_manager.verify(plain_password, self.password)
    
    
class Database:
    
    def __init__(self):
        self._users = {}
    
    async def add_user(self, username: str, email: str, password: str, admin: Optional[bool]) -> Optional[User]:
        if not self._email_and_name_unique(email, username):
            return None   
        user_created = User(username=username, email=email, password=password)
        
        if isinstance(admin, bool):
            user_created.admin = admin
            
        self._users[user_created.udi] = user_created
        return user_created
    
    async def list_users(self) -> List[Optional[User]]:
        return list(self._users.values())
    
    async def find_user_by_udi(self, udi: UUID1) -> Optional[User]:
        return self._users.get(udi)

    async def find_user_by_creds(self, name: str, plain_pass: str) -> Optional[User]:
        for _, user in self._users.items():
            if user.username == name and user.check_password(plain_pass):
                return user
            
        return None
            
    async def upd_user(self, u: User, upd_data: Dict[str, str]) -> bool:       
        new_username, new_email = upd_data["username"], upd_data["email"]
        if not self._email_and_name_unique(new_email, new_username):
            return False
            
        u.username = new_username
        u.email = new_email
        u.updated_at = datetime.now()
        u.set_password(upd_data["password"])
        return True
    
    async def del_user(self, udi: UUID1) -> bool:
        u = await self.find_user_by_udi(udi)
        if not u:
            return False
        self._users.pop(u.udi)
        return True
    
    def _email_and_name_unique(self, email: str, name: str) -> bool:
        for _, user in self._users.items():
            if user.username == name or user.email == email:
                return False

        return True


db = Database()
