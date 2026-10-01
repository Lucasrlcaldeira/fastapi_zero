# asyncio: módulo do Python que roda código assíncrono (async/await).
import asyncio

from logging.config import fileConfig

# async_engine_from_config: cria um engine ASSÍNCRONO a partir das
# configurações do alembic.ini (o antigo engine_from_config era o
# síncrono, que não funciona com o driver aiosqlite).
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy import pool

from alembic import context
from fastapi_zero.settings import Settings
from fastapi_zero.models import table_registry

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
config.set_main_option('sqlalchemy.url', Settings().DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = table_registry.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    # Parte SÍNCRONA: o Alembic só sabe rodar migrações de forma
    # síncrona. Recebe uma conexão pronta e aplica as migrações.
    context.configure(
        connection=connection, target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    # Parte ASSÍNCRONA: abre a conexão com o banco usando o engine
    # assíncrono e "empresta" essa conexão para a parte síncrona.
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
        # run_sync: executa a função síncrona do_run_migrations
        # dentro da conexão assíncrona (a "ponte" entre os dois
        # mundos).


def run_migrations_online() -> None:
    # Funções async não rodam sozinhas: asyncio.run() cria o loop de
    # eventos, executa a corrotina até o fim e depois o encerra.
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
