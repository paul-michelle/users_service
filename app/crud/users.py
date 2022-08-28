from collections.abc import Sequence
from datetime import datetime
from typing import Optional

from pydantic import UUID4
from sqlalchemy.orm import Session

from app.models.users import User
from app.schemas.users import UserInfoIn, UserInfoUpd


class UserCRUD:
    
    def get(self, db: Session, _id: Optional[UUID4] = None, username: str = "") -> Optional[User]:
        if _id: 
            return db.query(User).filter(User.id == _id).first()
        return db.query(User).filter(User.username == username).first()
        
    def get_many(self, db: Session, skip: int, limit: int) -> Sequence[Optional[User]]:
        return db.query(User).offset(skip).limit(limit).all()
    
    def create(self, db: Session, data: UserInfoIn) -> User:
        u = User(username=data.username, email=data.email, admin=data.admin)  # type: ignore
        u.set_password(data.password)
        db.add(u)
        db.commit()
        db.refresh(u)
        return u

    def delete(self, db: Session, usr: User) -> None:
        db.delete(usr)
        db.commit()
    
    def update(self, db: Session, usr: User, upd_data: UserInfoUpd) -> None:
        if upd_data.email:
            usr.email = upd_data.email
        if upd_data.username:
            usr.username = upd_data.username
        if upd_data.password:
            usr.set_password(upd_data.password)
        usr.updated_at = datetime.utcnow()
        db.add(usr)
        db.commit()
    
    def deactivate(self, db: Session, usr: User) -> None:
        usr.active = False
        usr.updated_at = datetime.utcnow()
        db.add(usr)
        db.commit()
    
    def name_uniq(self, db: Session, username: str, _id: Optional[UUID4] = None) -> bool:
        if _id:
            return not db.query(User).filter(User.username == username, User.id != _id).first()
        return not db.query(User).filter(User.username == username).first()

    def email_uniq(self, db: Session, email: str, _id: Optional[UUID4] = None) -> bool:
        if _id:
            return not db.query(User).filter(User.email == email, User.id != _id).first()
        return not db.query(User).filter(User.email == email).first()
    
    def purge(self, db: Session) -> None:
        db.query(User).delete()
        db.commit()
    
    
user = UserCRUD()
