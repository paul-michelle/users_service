from email_validator import EMAIL_MAX_LENGTH
from sqlalchemy import Boolean, Column, DateTime, String, Table
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import metadata
from app.schemas.users import NAME_MAX_LENGTH

users = Table(
    "users",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("username", String(NAME_MAX_LENGTH), nullable=False, unique=True),
    Column("email", String(EMAIL_MAX_LENGTH), nullable=False, unique=True),
    Column("password", String(128), nullable=False),
    Column("active", Boolean, nullable=False, default=True),
    Column("admin", Boolean, nullable=False, default=False)
)
