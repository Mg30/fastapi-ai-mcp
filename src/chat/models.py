from datetime import datetime
from uuid import UUID, uuid4

from pydantic import field_validator
from sqlalchemy import String

from sqlmodel import Field, Relationship, SQLModel, JSON, Column


class Chat(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str
    created_at: datetime

    messages: list["Message"] | None = Relationship(
        back_populates="chat", cascade_delete=True
    )
    summaries: list["ChatSummary"] | None = Relationship(
        back_populates="chat", cascade_delete=True
    )
    assistant_id: UUID = Field(foreign_key="assistant.id")


class Message(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    date: datetime
    role: str
    content: str
    chat_id: UUID | None = Field(foreign_key="chat.id", default=None)

    chat: Chat | None = Relationship(back_populates="messages")

    @field_validator("role")
    @classmethod
    def _check_role(cls, v):
        if v not in ["assistant", "user"]:
            raise ValueError("should be either 'assistant' or 'user'")
        return v


class ChatSummary(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    summary: str
    created_at: datetime
    chat_id: UUID | None = Field(foreign_key="chat.id")

    chat: Chat | None = Relationship(back_populates="summaries")


class Assistant(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    description: str
    system_prompt: str
    model: str = Field(
        default="gpt-4o",
        description="OpenAI model to use for this assistant",
    )
    mcp_command: str | None = Field(nullable=True)
    mcp_args: list[str] | None = Field(sa_column=Column(JSON), default=None)
    temperature: float = Field(
        default=0.5, description="OpenAI temperature setting for this assistant"
    )
    max_tokens: int = Field(
        default=2000, description="OpenAI max tokens setting for this assistant"
    )
