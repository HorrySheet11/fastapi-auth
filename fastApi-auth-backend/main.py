from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from jose import jwt, JWTError
from passlib.context import CryptContext
from database import get_user, create_user

SECRET_KEY = "CHANGE_ME_IN_PRODUCTION"          # Use an env var in real apps
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

app = FastAPI(title="JWT App")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None

class UserPublic(BaseModel):
    username: str
    full_name: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def authenticate_user(email: str, password: str) -> Optional[dict]:
    user = get_user(email)
    if not user or not verify_password(password, user.password):
        return None
    return user