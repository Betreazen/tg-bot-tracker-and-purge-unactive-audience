from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.database.models import Base
import logging

logger = logging.getLogger(__name__)


class Database:
    """Database connection manager"""
    
    def __init__(self, database_url: str):
        """
        Initialize database connection
        
        Args:
            database_url: PostgreSQL connection string (postgresql+asyncpg://...)
        """
        self.engine = create_async_engine(
            database_url,
            echo=False,
            poolclass=NullPool,
        )
        self.session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
    async def create_tables(self):
        """Create all tables in the database"""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    async def drop_tables(self):
        """Drop all tables in the database"""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Error dropping database tables: {e}")
            raise
    
    async def close(self):
        """Close database connection"""
        await self.engine.dispose()
        logger.info("Database connection closed")
    
    def get_session(self) -> AsyncSession:
        """Get a new database session"""
        return self.session_maker()


# Global database instance
db: Database | None = None


async def init_db(database_url: str) -> Database:
    """
    Initialize database connection
    
    Args:
        database_url: PostgreSQL connection string
        
    Returns:
        Database instance
    """
    global db
    db = Database(database_url)
    await db.create_tables()
    return db


async def close_db():
    """Close database connection"""
    global db
    if db:
        await db.close()
        db = None


def get_db() -> Database:
    """Get global database instance"""
    if db is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return db
