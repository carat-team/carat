from alembic import context
from sqlalchemy import create_engine, pool

from carat_backend.settings import get_settings
from carat_backend.storage.tables import Base

# Tests pass their own database through `sqlalchemy.url`; otherwise the URL comes from the DB_* variables
url = context.config.get_main_option("sqlalchemy.url") or get_settings().database.url
target_metadata = Base.metadata

if context.is_offline_mode():
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    with create_engine(url, poolclass=pool.NullPool).connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
