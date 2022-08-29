from collections.abc import Sequence
from datetime import datetime
from typing import Dict, Optional, Union
from uuid import uuid4

from asyncpg import UniqueViolationError
from databases.backends.postgres import Record
from pydantic import UUID4
from sqlalchemy.orm import Session

from app.db.session import db
from app.db.utils import pass_manager
from app.models.users import users
from app.schemas.users import UserInfoUpd, UsrIn

UserAutoAssigned = Dict[str, Union[UUID4, datetime]]
UserAllAttrs     = Dict[str, Union[UUID4, datetime, str, bool]]


class UserCRUD:
    
    async def create(self, reg_data: UsrIn) -> Optional[UserAutoAssigned]:
        _id, = uuid4()
        _now = datetime.utcnow()
        
        q = users.insert().values(
            id=_id,
            created_at=_now,
            updated_at=_now,
            username=reg_data.username, 
            email=reg_data.email,  
            password=pass_manager.hash(reg_data.password),
            admin=reg_data.admin,
            active=True
        )
        
        try:    
            await db.execute(q)
        except UniqueViolationError:
            return None
        
        return {"id": _id, "created_at": _now, "updated_at": _now}

    async def get(self, _id: Optional[UUID4] = None, username: str = "") -> Optional[Record]:
        q = users.select().where(user.c.id == _id)
        if username: 
            q = users.select().where(user.c.username == username) 
        return await db.fetch_one(q)
        # query_res = await db.fetch_one(q)
        
        # if not query_res:
        #     return None
        
        # return dict(query_res._mapping)
        
    async def get_many(self, skip: int, limit: int) -> Sequence[Optional[Record]]:
        q = users.select().offset(skip).limit(limit)
        return await db.fetch_all(q)
    
    async def delete(self, id: UUID4) -> Optional[bool]:
        q = users.delete().where(users.c.id == id).returning(True)
        return await db.execute(q)

    async def update(self, _id: UUID4, upd_data: UserInfoUpd) -> bool:
        success = True
        
        q, vals = users.update().where(users.c.id == _id), {}
       
        if upd_data.email:
            vals["email"] = upd_data.email
        if upd_data.username:
            vals["username"] = upd_data.username 
        if upd_data.password:
            vals["password"] = pass_manager.hash(upd_data.password)
        vals["updated_at"] = datetime.utcnow()
        
        try:
            await db.execute(q, vals)
        except UniqueViolationError:
            success = False

        return success
    
    async def deactivate(self, _id: UUID4) -> None:
        q = users.update().where(users.c.id == _id)
        vals = {"active": False, "updated_at": datetime.utcnow()}
        await db.execute(q, vals)
        
    async def purge(self) -> None:
        await db.execute(users.delete())
    
    
user = UserCRUD()
