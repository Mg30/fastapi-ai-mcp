from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status
from src.chat.models import Assistant
from src.chat.services import AssistantService
from src.container import Container

router = APIRouter(prefix="/assistants")


@router.get("/{assistant_id}")
@inject
def get_assistant(
    assistant_id: UUID,
    assistant_service: AssistantService = Depends(Provide[Container.assistant_service]),
) -> Assistant:
    return assistant_service.get_assistant(assistant_id)


@router.post("/", status_code=status.HTTP_201_CREATED)
@inject
def create_assistant(
    assistant: Assistant,
    assistant_service: AssistantService = Depends(Provide[Container.assistant_service]),
) -> Assistant:
    return assistant_service.create(assistant)


@router.get("/")
@inject
def list_assistant(
    assistant_service: AssistantService = Depends(Provide[Container.assistant_service]),
) -> list[Assistant]:
    return assistant_service.list_assistants()
