import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Use postgresql+asyncpg scheme
DB_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(
    DB_URL, 
    echo=False, 
    pool_size=5, 
    max_overflow=10
)

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db_session():
    """Dependency to get a DB session."""
    async with AsyncSessionLocal() as session:
        yield session