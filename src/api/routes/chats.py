from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from src.chat.models import Chat, Message
from src.chat.schemas import ChatUpdate
from src.chat.services import ChatService
from src.container import Container

router = APIRouter(prefix="/chats")


@router.get("/{chat_id}")
@inject
def get_chat(
    chat_id: UUID, chat_service: ChatService = Depends(Provide[Container.chat_service])
) -> Chat:
    return chat_service.get_chat(chat_id)


@router.get("/")
@inject
def get_chats(
    chat_service: ChatService = Depends(Provide[Container.chat_service]),
) -> list[Chat]:
    return chat_service.get_chats()


@router.post("/", status_code=status.HTTP_201_CREATED)
@inject
def create_chat(
    new_chat: Chat, chat_service: ChatService = Depends(Provide[Container.chat_service])
) -> Chat:
    return chat_service.create_chat(new_chat)


@router.post("/{chat_id}/completions")
@inject
async def complete_chat(
    chat_id: UUID,
    message: Message,
    chat_service: ChatService = Depends(Provide[Container.chat_service]),
) -> StreamingResponse:
    async def _stream_generator():
        async for chunk in chat_service.complete_chat(chat_id=chat_id, message=message):
            yield chunk

    return StreamingResponse(_stream_generator(), media_type="text/plain")


@router.post("/{chat_id}/message", status_code=status.HTTP_201_CREATED)
@inject
def append_message(
    chat_id: str,
    message: Message,
    chat_service: ChatService = Depends(Provide[Container.chat_service]),
) -> Message:
    return chat_service.create_message_for(chat_id=chat_id, message=message)


@router.get("/{chat_id}/messages")
@inject
def get_messages(
    chat_id: str, chat_service: ChatService = Depends(Provide[Container.chat_service])
) -> list[Message]:
    return chat_service.get_chat_message(chat_id)


@router.put("/{chat_id}", status_code=status.HTTP_200_OK)
@inject
def update_chat(
    chat_id: UUID,
    chat_update: ChatUpdate,
    chat_service: ChatService = Depends(Provide[Container.chat_service]),
) -> Chat:
    # Retrieve the existing chat
    existing_chat = chat_service.get_chat(chat_id)
    if existing_chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")

    existing_chat.title = chat_update.title

    # Save the updated chat via the service/repository
    updated_chat = chat_service.update_chat(existing_chat)
    return updated_chat


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
def delete_chat(
    chat_id: UUID, chat_service: ChatService = Depends(Provide[Container.chat_service])
) -> None:
    success = chat_service.delete_chat(chat_id)
    if not success:
        raise HTTPException(status_code=404, detail="Chat not found")
    return None
