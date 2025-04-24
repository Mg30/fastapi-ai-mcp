from dataclasses import dataclass
from typing import Callable
from uuid import UUID

from sqlmodel import Session, select

from .models import Assistant, Chat, ChatSummary, Message


@dataclass(slots=True)
class ChatRepository:
    session_factory: Callable[[], Session]

    def create(self, chat: Chat) -> Chat:
        with self.session_factory() as session:
            try:
                session.add(chat)
                session.commit()
                session.refresh(chat)
                return chat
            except Exception:
                session.rollback()
                raise

    def get_by_id(self, chat_id: UUID) -> Chat | None:
        with self.session_factory() as session:
            return session.get(Chat, chat_id)

    def get_all(self) -> list[Chat]:
        with self.session_factory() as session:
            return session.exec(select(Chat)).all()

    def update(self, chat: Chat) -> Chat:
        with self.session_factory() as session:
            try:
                session.add(chat)
                session.commit()
                session.refresh(chat)
                return chat
            except Exception as err:
                session.rollback()
                raise

    def delete(self, chat_id: UUID) -> bool:
        with self.session_factory() as session:
            chat = self.get_by_id(chat_id)
            if not chat:
                return False
            session.delete(chat)
            session.commit()
            return True


@dataclass(slots=True)
class MessageRepository:
    session_factory: Callable[[], Session]

    def create(self, message: Message) -> Message:
        with self.session_factory() as session:
            try:
                session.add(message)
                session.commit()
                session.refresh(message)
                return message
            except Exception:
                session.rollback()
                raise

    def get_by_id(self, message_id: UUID) -> Message | None:
        with self.session_factory() as session:
            return session.get(Message, message_id)

    def get_all(self) -> list[Message]:
        with self.session_factory() as session:
            return session.exec(select(Message)).all()

    def get_by_chat_id(self, chat_id: UUID) -> list[Message]:
        with self.session_factory() as session:
            statement = (
                select(Message).where(Message.chat_id == chat_id).order_by(Message.date)
            )
            return session.exec(statement).all()

    def update(self, message: Message) -> Message:
        with self.session_factory() as session:
            try:
                session.add(message)
                session.commit()
                session.refresh(message)
                return message
            except Exception:
                session.rollback()
                raise

    def delete(self, message_id: UUID) -> bool:
        with self.session_factory() as session:
            message = self.get_by_id(message_id)
            if not message:
                return False
            try:
                session.delete(message)
                session.commit()
                return True
            except Exception:
                session.rollback()
                raise


@dataclass(slots=True)
class ChatSummaryRepository:
    session_factory: Callable[[], Session]

    def create(self, summary: ChatSummary) -> ChatSummary:
        with self.session_factory() as session:
            try:
                session.add(summary)
                session.commit()
                session.refresh(summary)
                return summary
            except Exception:
                session.rollback()
                raise

    def get_by_id(self, summary_id: UUID) -> ChatSummary | None:
        with self.session_factory() as session:
            return session.get(ChatSummary, summary_id)

    def get_all(self) -> list[ChatSummary]:
        with self.session_factory() as session:
            return session.exec(select(ChatSummary)).all()

    def get_by_chat_id(self, chat_id: UUID) -> list[ChatSummary]:
        with self.session_factory() as session:
            statement = select(ChatSummary).where(ChatSummary.chat_id == chat_id)
            return session.exec(statement).all()

    def update(self, summary: ChatSummary) -> ChatSummary:
        with self.session_factory() as session:
            try:
                session.add(summary)
                session.commit()
                session.refresh(summary)
                return summary
            except Exception:
                session.rollback()
                raise

    def delete(self, summary_id: UUID) -> bool:
        with self.session_factory() as session:
            summary = self.get_by_id(summary_id)
            if not summary:
                return False
            try:
                session.delete(summary)
                session.commit()
                return True
            except Exception:
                session.rollback()
                raise


@dataclass(slots=True)
class AssistantRepository:
    session_factory: Callable[[], Session]

    def create(self, assistant: Assistant) -> Assistant:
        with self.session_factory() as session:
            try:
                session.add(assistant)
                session.commit()
                session.refresh(assistant)
                return assistant
            except Exception as e:
                session.rollback()
                raise e

    def get_by_id(self, assistant_id: UUID) -> Assistant | None:
        with self.session_factory() as session:
            return session.get(Assistant, assistant_id)

    def get_all(self) -> list[Assistant]:
        with self.session_factory() as session:
            statement = select(Assistant)
            return session.exec(statement).all()

    def update(self, assistant: Assistant) -> Assistant:
        with self.session_factory() as session:
            try:
                session.add(assistant)
                session.commit()
                session.refresh(assistant)
                return assistant
            except Exception as e:
                session.rollback()
                raise e

    def delete(self, assistant_id: UUID) -> bool:
        with self.session_factory() as session:
            assistant = self.get_by_id(assistant_id)
            if not assistant:
                return False
            session.delete(assistant)
            session.commit()
            return True
