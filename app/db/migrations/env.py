from logging.config import fileConfig as logConfigFromFile

from sqlalchemy import engine_from_config, pool
from sqlalchemy.sql.schema import MetaData
from alembic import context

from app.config import settings as s
from app.db.database import BaseModel

logConfigFromFile(context.config.config_file_name)

url = f"postgresql://{s.postgres_user}:{s.postgres_password}@{s.postgres_host}:{s.postgres_port}/{s.postgres_database}"
target_metadata: MetaData = BaseModel.metadata


def dry_run() -> None:
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_server_default=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def migrate() -> None:
    connectable = engine_from_config(
        {"sqlalchemy.url": url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    dry_run()
else:
    migrate()
    