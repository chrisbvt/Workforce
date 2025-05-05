from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool
import os
from dotenv import load_dotenv

load_dotenv()

# Get database type from environment
DATABASE_TYPE = os.getenv("DATABASE_TYPE", "postgresql")

# Get appropriate database URL based on type
if DATABASE_TYPE == "sqlite":
    # Use absolute path for SQLite database
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "crewai.db"))
    DATABASE_URL = f"sqlite+aiosqlite:///{db_path}"
    # SQLite specific configuration
    engine_kwargs = {
        "echo": True,
        "connect_args": {"check_same_thread": False}  # Required for SQLite
    }
else:
    DATABASE_URL = os.getenv("POSTGRES_URL")
    # PostgreSQL specific configuration
    engine_kwargs = {
        "echo": True,
        "poolclass": NullPool
    }

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    **engine_kwargs
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Create base class for models
Base = declarative_base()

# Dependency to get DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Initialize database
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Reset database (drop and recreate all tables)
async def reset_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all) 