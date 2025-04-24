from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes.assistants import router as assistant_router
from src.api.routes.chats import router as chat_router
from src.container import Container
from src.resources.settings import Settings


def create_app() -> FastAPI:
    container = Container()
    container.settings.from_pydantic(Settings())
    container.init_resources()

    app = FastAPI()

    # Enable CORS for all origins (development only)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins
        allow_credentials=True,
        allow_methods=["*"],  # Allow all methods
        allow_headers=["*"],  # Allow all headers
    )

    app.include_router(chat_router)
    app.include_router(assistant_router)
    app.container = container

    return app


app = create_app()
