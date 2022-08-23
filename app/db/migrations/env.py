from logging.config import fileConfig as get_log_config_from_file

from sqlalchemy.engine.url import URL
from sqlalchemy import engine_from_config, pool
from alembic import context

from app.config import settings
from app.db.database import BaseModel


get_log_config_from_file(context.config.config_file_name)

url = URL(
    drivername="postgresql+psycopg2",
    username=settings.postgres_user,
    password=settings.postgres_password,
    host=settings.postgres_host,
    port=settings.postgres_port,
    database=settings.postgres_database
)
target_metadata  = BaseModel.metadata
sa_configuration =  {
    "sqlalchemy.url": url,
    "sqlalchemy.poolclass": pool.NullPool
}

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
    connectable = engine_from_config(sa_configuration)
    
    with connectable.connect() as conn:
        context.configure(
            connection=conn, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    dry_run()
else:
    migrate()
    