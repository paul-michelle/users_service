from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import conn_string

engine = create_engine(conn_string, pool_pre_ping=True)
Session = sessionmaker(autoflush=False, bind=engine)
