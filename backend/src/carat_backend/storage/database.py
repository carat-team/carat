from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session, sessionmaker

SessionFactory = sessionmaker[Session]


def create_session_factory(database_url: URL | str) -> SessionFactory:
    return sessionmaker(create_engine(database_url, pool_pre_ping=True), expire_on_commit=False)
