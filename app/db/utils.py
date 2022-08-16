from passlib.context import CryptContext  # type: ignore

password_manager = CryptContext(schemes=["bcrypt"], deprecated="auto")
