"""SQLAlchemy engine and session helpers."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from sentinel_server.config import get_settings
from sentinel_server.models import Base

engine: Engine | None = None
SessionLocal: sessionmaker[Session] | None = None


def setup_engine(database_url: str | None = None) -> Engine:
    """Create (or recreate) the global engine/session factory."""
    global engine, SessionLocal
    url = database_url or get_settings().database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, pool_pre_ping=True, connect_args=connect_args)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return engine


def init_db(database_url: str | None = None) -> None:
    if engine is None or database_url is not None:
        setup_engine(database_url)
    assert engine is not None
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    if SessionLocal is None:
        setup_engine()
    assert SessionLocal is not None
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def db_ready() -> bool:
    try:
        if engine is None:
            setup_engine()
        assert engine is not None
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001
        return False
