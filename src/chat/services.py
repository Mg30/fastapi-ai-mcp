from dataclasses import dataclass
from uuid import UUID

from src.llm.config import OpenAIConfig
from src.llm.streaming import OpenAIStreaming
from src.mcp.utils import call_tool_factory, list_tools_factory

from mcp import StdioServerParameters

from .models import Assistant, Chat, Message
from .repositories import AssistantRepository, ChatRepository, MessageRepository


@dataclass(slots=True)
class ChatService:
    chat_repository: ChatRepository
    message_repository: MessageRepository
    assistant_repository: AssistantRepository
    llm_service: OpenAIStreaming

    def create_chat(self, new_chat: Chat) -> Chat:
        chat_created = self.chat_repository.create(new_chat)
        return chat_created

    def create_message_for(self, chat_id: UUID, message: Message) -> Message:
        message.chat_id = chat_id
        return self.message_repository.create(message)

    async def complete_chat(self, chat_id: UUID, message: Message):
        message.chat_id = chat_id
        self.message_repository.create(message)

        chat = self.chat_repository.get_by_id(chat_id)
        assistant = self.assistant_repository.get_by_id(chat.assistant_id)

        mcp = {}

        if (args := assistant.mcp_args) and (command := assistant.mcp_command):
            stdio_server_params = StdioServerParameters(command=command, args=args)

            mcp["list_tools"] = list_tools_factory(stdio_server_params)
            mcp["call_tool"] = call_tool_factory(stdio_server_params)

        llm_config = OpenAIConfig(
            model=assistant.model,
            temperature=assistant.temperature,
            max_tokens=assistant.max_tokens,
        )

        messages_history = self.message_repository.get_by_chat_id(chat_id=chat_id)

        messages_history = [
            dict(role=msg.role, content=msg.content) for msg in messages_history
        ]

        async for response in self.llm_service.stream(
            system_prompt=assistant.system_prompt,
            config=llm_config,
            messages=messages_history,
            **mcp,
        ):
            yield response

    def get_chat(self, chat_id: UUID) -> Chat:
        return self.chat_repository.get_by_id(chat_id)

    def get_chat_message(self, chat_id: UUID) -> list[Message]:
        return self.message_repository.get_by_chat_id(chat_id)

    def get_chats(self) -> list[Chat]:
        return self.chat_repository.get_all()

    def update_chat(self, chat: Chat) -> Chat:
        """
        Update the chat with the provided data.
        """
        return self.chat_repository.update(chat)

    def delete_chat(self, chat_id: UUID) -> bool:
        """
        Delete the chat by its id.
        Returns True if the chat was deleted, or False if it was not found.
        """
        return self.chat_repository.delete(chat_id)


@dataclass(slots=True)
class AssistantService:
    assistant_repository: AssistantRepository

    def create(self, assistant: Assistant) -> Assistant:
        return self.assistant_repository.create(assistant)

    def get_assistant(self, assistant_id: UUID) -> Assistant:
        return self.assistant_repository.get_by_id(assistant_id)

    def list_assistants(self) -> list[Assistant]:
        return self.assistant_repository.get_all()
