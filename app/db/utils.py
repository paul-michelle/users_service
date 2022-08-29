from passlib.context import CryptContext  # type: ignore

pass_manager = CryptContext(schemes=["bcrypt"], deprecated="auto")
