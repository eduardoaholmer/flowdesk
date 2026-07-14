"""Importa o `models.py` de toda feature para popular o registry declarativo
do SQLAlchemy antes do primeiro uso.

Necessário porque relationships entre features são declaradas por nome de
classe em string (ex.: `Project.issues: Mapped[list["Issue"]]`,
`Issue.comments: Mapped[list["Comment"]]`) e só resolvem se a classe alvo já
foi importada em algum lugar do processo — caso contrário o SQLAlchemy lança
`InvalidRequestError` na primeira instanciação/consulta que force a
configuração do mapper (`_check_configure()`), mesmo que o código que falhou
não tenha relação direta com a classe ausente.

Único ponto de import, reutilizado por `main.py` (app real) e por
`db/migrations/env.py` (autogenerate do Alembic) — evita manter a mesma lista
duplicada nos dois lugares (`CLAUDE.md` §1).
"""

from src.features.attachments import models as attachments_models  # noqa: F401
from src.features.auth import models as auth_models  # noqa: F401
from src.features.comments import models as comments_models  # noqa: F401
from src.features.issues import models as issues_models  # noqa: F401
from src.features.labels import models as labels_models  # noqa: F401
from src.features.notifications import models as notifications_models  # noqa: F401
from src.features.projects import models as projects_models  # noqa: F401
from src.features.teams import models as teams_models  # noqa: F401
from src.features.workspaces import models as workspaces_models  # noqa: F401
