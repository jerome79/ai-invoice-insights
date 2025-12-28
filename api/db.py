from __future__ import annotations

import os
from sqlmodel import SQLModel, create_engine, Session

def get_database_url() -> str:
    # default local path; override with DATABASE_URL if needed
    return os.getenv("DATABASE_URL", "sqlite:///./data/app.db")

engine = create_engine(
    get_database_url(),
    echo=False,
    connect_args={"check_same_thread": False} if get_database_url().startswith("sqlite") else {},
)

def init_db() -> None:
    SQLModel.metadata.create_all(engine)

def get_session() -> Session:
    return Session(engine)
