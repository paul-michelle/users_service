from logging.config import fileConfig as log_config_from_file

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy_utils import create_database, database_exists

from app.config import get_conn_url
from app.db.meta import metadata

ini = context.config.config_file_name
if ini:
   log_config_from_file(ini)

conn_string = get_conn_url(sync=True)

if not database_exists(conn_string):
    create_database(conn_string)
    
sa_configuration = {
    "sqlalchemy.url": conn_string,
    "sqlalchemy.poolclass": pool.NullPool
}
   
    
def dry_run() -> None:
    context.configure(
        url=conn_string,
        target_metadata=metadata,
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
            target_metadata=metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    dry_run()
else:
    migrate()
    