from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
import asyncio
from prisma import Prisma
from typing import Annotated
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import bcrypt

db = Prisma()

router = APIRouter(
  prefix="/users",
  tags=["users"],
  responses={404: {"description": "Not found"}}
)

# to get a string like this run:
# openssl rand -hex 32
# SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 30


fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$wagCPXjifgvUFBzq4hqe3w$CYaIb8sB+wtD+Vu/P4uod1+Qof8h+1g7bbDlBID48Rc",
        "disabled": False,
    }
}

def fake_hash_password(password: str):
    return "fakehashed" + password

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: str
    full_name: str | None = None
    isActive: bool | None = None
    password: str


class UserInDB(User):
    hashed_password: str

async def is_db_connected() -> bool:
    try:
        await db.execute_raw('SELECT 1')
        return True
    except Exception:
        return False

async def get_user(email: str, password: str):
    try:
        if await is_db_connected() == False:
            await db.connect()
        user = await db.user.find_unique(
        where={"email": email},
        )
        if bcrypt.checkpw(password.encode('utf-8'), user.password ): 
            return user
    except Exception:
        return None
    await db.disconnect()


    return user


def decode_token(token):
    salt = bcrypt.gensalt()
    hashed_token = bcrypt.hashpw(token, salt)
    return hashed_token


async def get_current_user(token: Annotated[User, Depends(oauth2_scheme)]):
    user = get_user(token.email, token.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.get("/users/me")
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user

@router.post("/user/signup", response_model=User)
async def create_user(user: UserInDB):
    if await is_db_connected() == False:
        await db.connect()
    if await db.user.find_unique(where={"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = await db.user.create(data=user.dict())
    await db.disconnect()
    return user