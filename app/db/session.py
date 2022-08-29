from databases import Database

from app.config import get_conn_url

db = Database(str(get_conn_url()))
