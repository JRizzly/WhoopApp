from __future__ import with_statement
import gevent.monkey
gevent.monkey.patch_all() # gunicorn is not around to do it for us.

import os
import sys

from alembic import context
from sqlalchemy import engine_from_config, pool
from logging.config import fileConfig

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

sys.path.append(os.path.expanduser("~/app"))

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
from app import create_app
app = create_app()
target_metadata = app.db.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url)

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    session = app.db.session
    context.configure(
                connection=session.connection(),
                target_metadata=target_metadata
                )

    try:
        context.run_migrations()
        session.commit()
    finally:
        session.rollback()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

