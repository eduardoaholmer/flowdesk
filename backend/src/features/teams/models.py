import enum
import uuid

from sqlalchemy import ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, domain_enum


class WorkflowStateCategory(enum.StrEnum):
    BACKLOG = "BACKLOG"
    UNSTARTED = "UNSTARTED"
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"


class Team(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "teams"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(nullable=False)
    key: Mapped[str] = mapped_column(nullable=False)

    members: Mapped[list["TeamMember"]] = relationship(back_populates="team")
    workflow_states: Mapped[list["WorkflowState"]] = relationship(back_populates="team")
    issue_counter: Mapped["TeamIssueCounter"] = relationship(back_populates="team")


Index(
    "uq_teams_workspace_id_key_active",
    Team.workspace_id,
    Team.key,
    unique=True,
    postgresql_where=text("deleted_at IS NULL"),
)


class TeamMember(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Invariante "membro do time já é membro do workspace" não é imposta por FK —
    validação cruzada entre agregados fica para o service (Sprint 3+), ver CLAUDE.md §5.
    """

    __tablename__ = "team_members"

    team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("teams.id", ondelete="RESTRICT"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    team: Mapped[Team] = relationship(back_populates="members")


Index(
    "uq_team_members_team_id_user_id_active",
    TeamMember.team_id,
    TeamMember.user_id,
    unique=True,
    postgresql_where=text("deleted_at IS NULL"),
)


class WorkflowState(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "workflow_states"

    team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("teams.id", ondelete="RESTRICT"), nullable=False
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(nullable=False)
    category: Mapped[WorkflowStateCategory] = mapped_column(
        domain_enum(WorkflowStateCategory), nullable=False
    )
    position: Mapped[int] = mapped_column(nullable=False)
    is_default: Mapped[bool] = mapped_column(nullable=False, default=False)

    team: Mapped[Team] = relationship(back_populates="workflow_states")


Index(
    "uq_workflow_states_team_id_name_active",
    WorkflowState.team_id,
    WorkflowState.name,
    unique=True,
    postgresql_where=text("deleted_at IS NULL"),
)
Index(
    "uq_workflow_states_team_id_position_active",
    WorkflowState.team_id,
    WorkflowState.position,
    unique=True,
    postgresql_where=text("deleted_at IS NULL"),
)
Index(
    "uq_workflow_states_team_id_default_active",
    WorkflowState.team_id,
    unique=True,
    postgresql_where=text("is_default AND deleted_at IS NULL"),
)


class TeamIssueCounter(TimestampMixin, Base):
    """Contador de número sequencial de issue por time — já previsto em
    docs/03-database.md §8 ("gerado por sequência dedicada por time... implementada
    via tabela de contador com SELECT ... FOR UPDATE no service"). Tabela separada de
    `teams` para não competir por lock de linha com edições de nome/etc do time.
    """

    __tablename__ = "team_issue_counters"

    team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("teams.id", ondelete="RESTRICT"), primary_key=True
    )
    next_number: Mapped[int] = mapped_column(nullable=False, default=1)

    team: Mapped[Team] = relationship(back_populates="issue_counter")
