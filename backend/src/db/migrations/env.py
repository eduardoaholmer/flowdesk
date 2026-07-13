import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from src.core.config import get_settings
from src.db.base import Base
from src.features.attachments import models as attachments_models  # noqa: F401,E402

# Importar cada features/*/models.py registra suas classes em Base.metadata —
# necessário aqui para que o autogenerate do Alembic enxergue todas as tabelas.
# Ordem segue a dependência de FK entre features (import isolado não cria ciclo).
from src.features.auth import models as auth_models  # noqa: F401,E402
from src.features.comments import models as comments_models  # noqa: F401,E402
from src.features.issues import models as issues_models  # noqa: F401,E402
from src.features.labels import models as labels_models  # noqa: F401,E402
from src.features.notifications import models as notifications_models  # noqa: F401,E402
from src.features.projects import models as projects_models  # noqa: F401,E402
from src.features.teams import models as teams_models  # noqa: F401,E402
from src.features.workspaces import models as workspaces_models  # noqa: F401,E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    return get_settings().database_url


def run_migrations_offline() -> None:
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def _do_run_migrations(connection: object) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)  # type: ignore[arg-type]
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable: AsyncEngine = create_async_engine(get_url())

    async with connectable.connect() as connection:
        await connection.run_sync(_do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
