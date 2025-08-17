import time
from datetime import datetime
from enum import Enum, StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Index, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel


class TaskPriority(int, Enum):
    HIGH = 1
    MIDDLE = 2
    LOW = 3


class SourceType(StrEnum):
    EMAIL = "email"
    CALENDAR = "calendar"
    SLACK = "slack"
    TEAMS = "teams"
    DISCORD = "discord"
    GITHUB_ISSUE = "github_issue"
    GITHUB_PR = "github_pr"
    JIRA = "jira"
    TRELLO = "trello"
    ASANA = "asana"
    NOTION = "notion"
    LINEAR = "linear"
    CLICKUP = "clickup"
    OTHER = "other"


class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id: int | None = Field(default=None, primary_key=True)
    uuid: UUID = Field(default_factory=uuid4, index=True)
    created_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    email: str | None = Field(nullable=True, index=True)
    name: str | None = Field(nullable=True)
    clerk_sub: str = Field(nullable=True, unique=True, index=True)

    google_oauth_tokens: list["GoogleOAuthToken"] = Relationship(back_populates="user")
    tasks: list["Tasks"] = Relationship(back_populates="user")
    ai_chat_usage: list["AIChatUsage"] = Relationship(back_populates="user")
    chat_threads: list["ChatThread"] = Relationship(back_populates="user")


class GoogleOAuthToken(SQLModel, table=True):
    __tablename__ = "google_oauth_tokens"
    __table_args__ = {"extend_existing": True}

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)

    access_token: str = Field(nullable=False)
    refresh_token: str | None = Field(nullable=True)
    token_type: str = Field(default="Bearer")
    expires_at: float | None = Field(nullable=True)
    scope: str | None = Field(nullable=True)

    created_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    updated_at: float = Field(default_factory=lambda: datetime.now().timestamp())

    google_user_id: str | None = Field(nullable=True, index=True)
    google_email: str | None = Field(nullable=True)

    user: User = Relationship(back_populates="google_oauth_tokens")


class Tasks(SQLModel, table=True):
    __tablename__ = "tasks"
    __table_args__ = {"extend_existing": True}

    id: int | None = Field(default=None, primary_key=True)
    uuid: UUID = Field(default_factory=uuid4, index=True)
    created_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    updated_at: float = Field(default_factory=lambda: datetime.now().timestamp())

    user_id: int = Field(foreign_key="users.id")
    user: User = Relationship(back_populates="tasks")

    title: str
    description: str | None = Field(nullable=True)
    completed: bool = Field(default=False)
    expires_at: float | None = Field(default=None, nullable=True)
    priority: TaskPriority | None = Field(default=None, nullable=True, index=True)

    sources: list["TaskSource"] = Relationship(back_populates="task")


class TaskSource(SQLModel, table=True):
    __tablename__ = "task_sources"
    __table_args__ = {"extend_existing": True}

    id: int | None = Field(default=None, primary_key=True)
    uuid: UUID = Field(default_factory=uuid4, index=True)
    created_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    updated_at: float = Field(default_factory=lambda: datetime.now().timestamp())

    task_id: int = Field(foreign_key="tasks.id")
    task: Tasks = Relationship(back_populates="sources")

    source_type: SourceType = Field(index=True)
    source_url: str | None = Field(nullable=True)
    source_id: str | None = Field(nullable=True, index=True)  # 外部システムでのID
    title: str | None = Field(nullable=True)
    content: str | None = Field(nullable=True)
    extra_data: str | None = Field(nullable=True)  # JSON形式で追加情報を保存


class AIChatUsage(SQLModel, table=True):
    __tablename__ = "ai_chat_usage"
    __table_args__ = (
        UniqueConstraint("user_id", "usage_date", name="uq_user_date"),
        Index("idx_user_date_fast", "user_id", "usage_date"),
        {"extend_existing": True},
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    usage_date: str = Field(index=True)  # YYYY-MM-DD format
    usage_count: int = Field(default=0)
    created_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    updated_at: float = Field(default_factory=lambda: datetime.now().timestamp())

    # Relationship to User
    user: User = Relationship(back_populates="ai_chat_usage")


class ChatThread(SQLModel, table=True):
    __tablename__ = "chat_threads"
    __table_args__ = (
        Index("idx_chat_threads_user_id", "user_id"),
        Index("idx_chat_threads_uuid", "uuid"),
        Index("idx_chat_threads_updated_at", "updated_at"),
        Index("idx_chat_threads_user_updated_desc", "user_id", "updated_at"),
        {"extend_existing": True},
    )

    id: int | None = Field(default=None, primary_key=True)
    uuid: UUID = Field(default_factory=uuid4, index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    title: str | None = Field(nullable=True)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)

    # Relationships
    user: User = Relationship(back_populates="chat_threads")
    messages: list["ChatMessage"] = Relationship(
        back_populates="thread",
        sa_relationship_kwargs={"order_by": "ChatMessage.created_at", "cascade": "all, delete-orphan"},
    )


class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_messages"
    __table_args__ = (
        Index("idx_chat_messages_thread_id", "thread_id"),
        Index("idx_chat_messages_created_at", "created_at"),
        Index("idx_chat_messages_thread_created", "thread_id", "created_at"),
        Index("idx_chat_messages_thread_created_desc", "thread_id", "created_at"),
        Index("idx_chat_messages_uuid", "uuid"),
        Index("idx_chat_messages_role", "role"),
        {"extend_existing": True},
    )

    id: int | None = Field(default=None, primary_key=True)
    uuid: UUID = Field(default_factory=uuid4, index=True)
    thread_id: int = Field(foreign_key="chat_threads.id", index=True)
    role: str = Field(index=True)  # OpenAI API compliant: "user", "assistant", "system"
    content: str
    created_at: float = Field(default_factory=time.time, index=True)

    # Relationship
    thread: ChatThread = Relationship(back_populates="messages")


metadata = SQLModel.metadata
