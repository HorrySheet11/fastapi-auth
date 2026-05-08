from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import asyncio
from prisma import Prisma
from typing import Optional
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm 
from jose import jwt
import os
from dotenv import load_dotenv

load_dotenv()
env = os.getenv

db = Prisma()

router = APIRouter(
    prefix="/items",
    tags=["items"],
    responses={404: {"description": "Not found"}}
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES")

class Item(BaseModel):
  text: str
  is_done: bool = False

async def is_db_connected() -> bool:
    try:
        await db.execute_raw('SELECT 1')
        return True
    except Exception:
        await db.connect()
        return False

@router.get("/")
async def read_items():
    if await is_db_connected() == False:
      await db.connect()
    print("read_items")
    items = await db.items.find_many()
    await db.disconnect()
    return items

@router.post("/")
async def create_item(item: Item, token: str = Depends(oauth2_scheme)):
  payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
  user: Optional[str] = payload.get("sub")
  await is_db_connected()
      # await db.connect()
  data = await db.items.create(
    data={
      "name": item.text,
      "isDone": item.is_done
    }
  )
  await db.disconnect()
  return data