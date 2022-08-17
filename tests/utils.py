from typing import Dict, Any, Tuple
from datetime import datetime
from requests import Response

from app.db.mem import User, db


class Resp:
    def __init__(self, r: Response) -> None:
        self._r = r
    
    def __enter__(self) -> Dict[str, Any]:
        resp_data = self._r.json()
        resp_data["status"] = self._r.status_code
        return resp_data
    
    def __exit__(self, *args) -> None:
        return


def fake_user() -> Tuple[User ,str]:
    timestamp = datetime.utcnow().timestamp()
    name = f"Rob{timestamp}"
    email = f"rob{timestamp}@gmail.com"
    pwd = f"!Pass{timestamp}"
    u = User(username=name, email=email,password=pwd)
    db.add_user_obj(u)  # type: ignore
    return u, pwd


def auth_headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
