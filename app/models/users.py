from datetime import datetime
from uuid import uuid4

from email_validator import EMAIL_MAX_LENGTH
from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import BaseModel
from app.db.utils import password_manager
from app.schemas.users import NAME_MAX_LENGTH


class User(BaseModel):
 
    __tablename__ = "users"
    
    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    username   = Column(String(NAME_MAX_LENGTH), nullable=False, unique=True)
    email      = Column(String(EMAIL_MAX_LENGTH), nullable=False, unique=True)
    password   = Column(String(128), nullable=False)
    active     = Column(Boolean, nullable=False, default=True)
    admin      = Column(Boolean, nullable=False, default=False)

    def set_password(self, plain_text: str) -> None:
        self.password = password_manager.hash(plain_text)

    def check_password(self, plain_password: str) -> bool:
        return password_manager.verify(plain_password, self.password)
