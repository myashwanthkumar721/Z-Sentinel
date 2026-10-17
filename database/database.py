from sqlalchemy import create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    sessionmaker,
)

from config.settings import settings


class Base(
    DeclarativeBase
):
    pass


engine = create_engine(
    settings.database_url,
    connect_args={
        "check_same_thread": False
    },
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def init_db() -> None:

    from database.models import Transaction

    Base.metadata.create_all(
        bind=engine
    )