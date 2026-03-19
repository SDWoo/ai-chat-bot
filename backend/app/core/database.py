from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import structlog

from app.core.config import settings

logger = structlog.get_logger()

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    logger.info("Initializing database")
    Base.metadata.create_all(bind=engine)

    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    if "messages" in inspector.get_table_names():
        cols = [c["name"] for c in inspector.get_columns("messages")]
        if "image_url" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE messages ADD COLUMN image_url VARCHAR"))
            logger.info("Added image_url column to messages table")

    logger.info("Database initialized")
