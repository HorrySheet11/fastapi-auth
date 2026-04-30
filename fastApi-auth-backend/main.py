from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from jose import jwt, JWTError
from passlib.context import CryptContext
from database import get_user, create_user
import bcrypt

SECRET_KEY = "CHANGE_ME_IN_PRODUCTION"          # Use an env var in real apps
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

app = FastAPI(title="JWT App")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class UserCreate(BaseModel):
    email: str = Field(..., min_length=3, max_length=20)
    password: str = Field(..., min_length=6)

class UserPublic(BaseModel):
    email: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

def hash_password(password: str):
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)  # rounds=12 is a good balance of security and performance
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed


def verify_password(plain: str, hashed: str) -> bool:
    # return pwd_context.verify(plain, hashed)
    return bcrypt.checkpw(plain.encode('utf-8'), hashed)

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

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserPublic:
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user: Optional[str] = payload.get("sub")
        if user is None:
            raise cred_exc
    except JWTError:
        raise cred_exc
    user = get_user(user.email)
    if not user:
        raise cred_exc
    return UserPublic(email=user["email"])


# FIXME: ValueError: password cannot be longer than 72 bytes
@app.post("/register", status_code=201, summary="Create a new user")
async def register_user(body: UserCreate):
    hashed = hash_password(body.password)
    await create_user(body.email, hashed)
    return {"message": "User registered successfully"}

@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.email, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token({"sub": user["email"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me", response_model=UserPublic, summary="Get my profile (protected)")
def read_me(current_user: UserPublic = Depends(get_current_user)):
    return current_user