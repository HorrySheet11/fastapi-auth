from prisma import Prisma
from fastapi import HTTPException
from typing import Optional
db = Prisma()

async def is_db_connected() -> bool:
  try:
    await db.execute_raw('SELECT 1')
    return True
  except Exception:
    return False
  
async def connect_db() -> None:
  try:
    await db.connect()
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
  
async def get_user(email: str):
  try:
    if is_db_connected() == False:
      await connect_db()
    user = await db.user.find_unique(where={"email": email})
    return user
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
  finally:
    await db.disconnect()

async def create_user(email: str, password ):
    try:
      if is_db_connected() == False:
        await connect_db()  
      user = await db.user.create(data={
        "email": email, "password": password})
    except Exception as e:
        raise HTTPException(status_code=409, detail=str(e))
    finally:
      await db.disconnect()