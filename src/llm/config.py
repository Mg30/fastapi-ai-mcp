from pydantic import BaseModel


class OpenAIConfig(BaseModel):
    """Configuration for OpenAI model settings."""

    model: str
    temperature: float
    max_tokens: int
