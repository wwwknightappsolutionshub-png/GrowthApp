from app.core.database import engine, Base
from sqlalchemy import text
import asyncio

async def test():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = [r[0] for r in result.fetchall()]
        print("Tables:", tables)
    
asyncio.run(test())
