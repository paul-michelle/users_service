from typing import List, Optional

from pydantic import UUID4
from sqlalchemy.orm import Session

from app.models.users import User
from app.schemas.users import UserInfoIn


class UserCRUD:
    
    def get(self, db: Session, id: UUID4) -> Optional[User]:
        return db.query(User).filter(User.id == id).first()
    
    def get_many(self, db: Session, skip: int, limit: int) -> List[Optional[User]]:
        return db.query(User).offset(skip).limit(limit).all()
    
    def create(self, db: Session, data: UserInfoIn) -> User:
        u = User(username=data.username, email=data.email, admin=data.admin)
        u.set_password(data.password)
        db.add(u); db.commit(); db.refresh(u)
        return u

    def delete(self, db: Session, usr: User) -> None:
        db.delete(usr)
        db.commit()
    
    def update(self, db: Session, usr: User, upd_data: UserInfoIn) -> None:
        if upd_data.email:
            usr.email = upd_data.email
        if upd_data.username:
            usr.username = upd_data.username
        if upd_data.password:
            usr.set_password(upd_data.password)
        db.add(usr)
        db.commit()
        
    def email_uniq(self, db: Session, email: str, _id: UUID4) -> bool:
        return not db.query(User).filter(User.email == email, User.id != _id).first()
    
    def name_uniq(self, db: Session, username: str, _id: UUID4) -> bool:
        return not db.query(User).filter(User.username == username, User.id != _id).first()
    
    
user = UserCRUD()