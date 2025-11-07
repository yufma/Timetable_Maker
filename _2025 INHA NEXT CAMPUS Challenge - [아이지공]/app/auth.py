from passlib.context import CryptContext
from fastapi import Request
from typing import Optional
from starlette.datastructures import Secret

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

SECRET = Secret("change-this-secret-in-prod")
SESSION_KEY = "user_id"

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)

def login_user(request: Request, user_id: int) -> None:
    request.session[SESSION_KEY] = int(user_id)

def logout_user(request: Request) -> None:
    request.session.pop(SESSION_KEY, None)

def current_user_id(request: Request) -> Optional[int]:
    return request.session.get(SESSION_KEY)
