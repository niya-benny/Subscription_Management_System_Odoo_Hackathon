import os, hashlib, hmac, secrets, datetime as dt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .database import get_db
from .models import User

SECRET = os.getenv("SECRET_KEY", "dev-secret-change-me")
bearer = HTTPBearer(auto_error=False)

def hash_pw(pw: str) -> str:
    salt = secrets.token_hex(8)
    return salt + "$" + hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 120_000).hex()

def verify_pw(pw: str, stored: str) -> bool:
    salt, h = stored.split("$")
    return hmac.compare_digest(h, hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 120_000).hex())

def make_token(user: User) -> str:
    exp = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=12)
    return jwt.encode({"sub": str(user.id), "role": user.role, "exp": exp}, SECRET, algorithm="HS256")

def current_user(cred: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)) -> User:
    if not cred:
        raise HTTPException(401, "Not authenticated")
    try:
        data = jwt.decode(cred.credentials, SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid or expired token")
    user = db.get(User, int(data["sub"]))
    if not user:
        raise HTTPException(401, "User not found")
    return user

def require(*roles: str):
    def dep(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(403, "Forbidden for role " + user.role)
        return user
    return dep
