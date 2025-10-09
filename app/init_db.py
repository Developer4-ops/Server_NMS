import asyncio
from main import Base, engine  # Import your Base and engine from main.py

async def init_db():
    async with engine.begin() as conn:
        # Create all tables defined in Base.metadata
        await conn.run_sync(Base.metadata.create_all)
    print("All tables created successfully!")

if __name__ == "__main__":
    asyncio.run(init_db())
