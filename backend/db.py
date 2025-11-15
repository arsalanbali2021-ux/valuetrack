"""
ValueTrack — Database Session Management
SQLAlchemy engine + scoped session for Flask request lifecycle.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base
from config import Config

engine = create_engine(
    Config.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=Config.DEBUG
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
db_session = scoped_session(SessionLocal)

Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    """Import models and create tables (for dev convenience)."""
    import models  # noqa: F401 — registers models with Base
    Base.metadata.create_all(bind=engine)


def shutdown_session(exception=None):
    """Remove scoped session at end of request."""
    db_session.remove()
