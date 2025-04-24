from pydantic import BaseModel


class ChatUpdate(BaseModel):
    title: str
