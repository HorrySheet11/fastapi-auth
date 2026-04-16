from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import asyncio
from prisma import Prisma

db = Prisma()

router = APIRouter(
  prefix="/users",
  tags=["users"],
  responses={404: {"description": "Not found"}}
)

class user(BaseModel):
  username: str
  password: str
  isActive: bool

async def is_db_connected() -> bool:
    try:
        await db.execute_raw('SELECT 1')
        return True
    except Exception:
        return False

@router.get("/")
async def read_users():
  if await is_db_connected() == False:
      await db.connect()
  users = await db.users.find_many()
  await db.disconnect()
  return users