from dependency_injector import containers, providers
from openai import AsyncOpenAI
from src.chat.repositories import (
    AssistantRepository,
    ChatRepository,
    ChatSummaryRepository,
    MessageRepository,
)
from src.chat.services import AssistantService, ChatService
from src.llm.completions import OpenAI
from src.llm.streaming import OpenAIStreaming
from src.resources.database import pg_engine, session_factory


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(packages=[".api.routes"])
    settings = providers.Configuration()

    engine = providers.Resource(pg_engine, settings=settings)

    openai_client = providers.Factory(AsyncOpenAI, api_key=settings.OPENAI_API_KEY)

    llm_streaming = providers.Factory(
        OpenAIStreaming,
        client=openai_client,
    )
    llm = providers.Factory(OpenAI, client=openai_client)
    session = providers.Factory(session_factory, engine=engine)
    chat_repo = providers.Factory(ChatRepository, session_factory=session)
    chat_msg_repo = providers.Factory(MessageRepository, session_factory=session)
    chat_summary_repo = providers.Factory(
        ChatSummaryRepository, session_factory=session
    )
    assistant_repo = providers.Factory(AssistantRepository, session_factory=session)

    chat_service = providers.Factory(
        ChatService,
        chat_repository=chat_repo,
        message_repository=chat_msg_repo,
        assistant_repository=assistant_repo,
        llm_service=llm_streaming,
    )

    assistant_service = providers.Factory(
        AssistantService, assistant_repository=assistant_repo
    )
