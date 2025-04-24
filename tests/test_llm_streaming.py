from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, List
from unittest.mock import AsyncMock, create_autospec

import pytest

# Import the class and related types to test
from openai import AsyncOpenAI
from openai.resources.chat import AsyncChat
from openai.resources.chat.completions import AsyncCompletions
from src.llm.config import OpenAIConfig
from src.llm.streaming import OpenAIStreaming  # Adjust the import path as necessary

from mcp.types import CallToolResult, ListToolsResult, Tool


# Define mock classes for response chunks
@dataclass
class ChoiceDeltaToolCallFunction:
    name: str = None
    arguments: str = ""


@dataclass
class ChoiceDeltaToolCall:
    id: str = None
    function: ChoiceDeltaToolCallFunction = field(
        default_factory=ChoiceDeltaToolCallFunction
    )
    type: str = "function"


@dataclass
class ChoiceDelta:
    content: str = ""
    tool_calls: List[ChoiceDeltaToolCall] = None


@dataclass
class Choice:
    delta: ChoiceDelta
    index: int = 0
    finish_reason: str = None


@dataclass
class ChatCompletionChunk:
    id: str
    choices: List[Choice]
    created: int
    model: str
    object: str


# Fixtures


@pytest.fixture
def openai_config():
    return OpenAIConfig(
        model="gpt-4",
        temperature=0.7,
        max_tokens=1000,
    )


@pytest.fixture
def mock_client():
    client = create_autospec(AsyncOpenAI, instance=True)
    client.chat = create_autospec(AsyncChat, instance=True)
    client.chat.completions = create_autospec(AsyncCompletions, instance=True)
    return client


@pytest.fixture
def mock_call_tool():
    return AsyncMock(spec=Callable[..., Coroutine[Any, Any, CallToolResult]])


@pytest.fixture
def mock_list_tools():
    return AsyncMock(spec=Callable[..., Coroutine[Any, Any, ListToolsResult]])


@pytest.fixture
def openai_streaming(mock_client):
    return OpenAIStreaming(
        client=mock_client,
    )


# Test Functions


@pytest.mark.asyncio
async def test_stream_no_tools(
    openai_streaming: OpenAIStreaming, mock_client, openai_config
):
    # Prepare test data
    system_prompt = "You are a helpful assistant."
    messages = [{"role": "user", "content": "Hello"}]
    expected_chunks = ["Hello", "World"]

    # Mock list_tools to return no tools
    mock_list_tools.return_value = ListToolsResult(tools=[])

    # Create response chunks
    async def mock_response_create(*args, **kwargs):
        stream = [
            ChatCompletionChunk(
                id="chunk_1",
                choices=[
                    Choice(
                        delta=ChoiceDelta(content="Hello"),
                        index=0,
                        finish_reason=None,
                    )
                ],
                created=1234567890,
                model="gpt-4",
                object="chat.completion.chunk",
            ),
            ChatCompletionChunk(
                id="chunk_2",
                choices=[
                    Choice(
                        delta=ChoiceDelta(content="World"),
                        index=0,
                        finish_reason="stop",
                    )
                ],
                created=1234567891,
                model="gpt-4",
                object="chat.completion.chunk",
            ),
        ]

        async def generator():
            for chunk in stream:
                yield chunk

        return generator()

    # Configure the mock's create method
    mock_client.chat.completions.create.return_value = mock_response_create()

    # Test streaming
    received_chunks = []
    async for chunk in openai_streaming.stream(
        system_prompt, openai_config, messages=messages
    ):
        received_chunks.append(chunk)

    assert received_chunks == expected_chunks


@pytest.mark.asyncio
async def test_stream_with_tool_calls(
    openai_streaming: OpenAIStreaming,
    mock_client,
    mock_call_tool,
    mock_list_tools,
    openai_config,
):
    # Prepare test data
    system_prompt = "You are a helpful assistant."
    messages = [{"role": "user", "content": "Perform a calculation"}]

    # Define a tool using the updated Tool class
    calculator_tool = Tool(
        name="calculator",
        description="Performs basic calculations",
        inputSchema={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate",
                }
            },
            "required": ["expression"],
        },
    )

    mock_list_tools.return_value = ListToolsResult(tools=[calculator_tool])

    # Mock call_tool to return a CallToolResult
    mock_call_tool.return_value = (
        "calculator",
        "id1111",
        CallToolResult(content=[{"type": "text", "text": "42"}]),
    )

    # Create first response chunks with a tool call
    async def mock_response_create_first(*args, **kwargs):
        stream = [
            ChatCompletionChunk(
                id="chunk_1",
                choices=[
                    Choice(
                        delta=ChoiceDelta(content="Calculating..."),
                        index=0,
                        finish_reason=None,
                    )
                ],
                created=1234567890,
                model="gpt-4",
                object="chat.completion.chunk",
            ),
            ChatCompletionChunk(
                id="chunk_2",
                choices=[
                    Choice(
                        delta=ChoiceDelta(
                            tool_calls=[
                                ChoiceDeltaToolCall(
                                    id="call_123",
                                    function=ChoiceDeltaToolCallFunction(
                                        name="calculator",
                                        arguments='{"expression": "6 * 7"}',
                                    ),
                                    type="function",
                                )
                            ]
                        ),
                        index=0,
                        finish_reason="tool_calls",
                    )
                ],
                created=1234567891,
                model="gpt-4",
                object="chat.completion.chunk",
            ),
            ChatCompletionChunk(
                id="chunk_3",
                choices=[
                    Choice(
                        delta=ChoiceDelta(content="The answer is "),
                        index=0,
                        finish_reason=None,
                    )
                ],
                created=1234567892,
                model="gpt-4",
                object="chat.completion.chunk",
            ),
            ChatCompletionChunk(
                id="chunk_4",
                choices=[
                    Choice(
                        delta=ChoiceDelta(content="42"),
                        index=0,
                        finish_reason="stop",
                    )
                ],
                created=1234567893,
                model="gpt-4",
                object="chat.completion.chunk",
            ),
        ]

        async def generator():
            for chunk in stream:
                yield chunk

        return generator()

    # Create second response chunks without tool calls
    async def mock_response_create_second(*args, **kwargs):
        stream = [
            ChatCompletionChunk(
                id="chunk_5",
                choices=[
                    Choice(
                        delta=ChoiceDelta(content="The answer is 42"),
                        index=0,
                        finish_reason="stop",
                    )
                ],
                created=1234567894,
                model="gpt-4",
                object="chat.completion.chunk",
            )
        ]

        async def generator():
            for chunk in stream:
                yield chunk

        return generator()

    # Configure the mock's create method with distinct responses
    mock_client.chat.completions.create.side_effect = [
        mock_response_create_first(),
        mock_response_create_second(),
    ]

    # Test streaming
    received_chunks = []
    async for chunk in openai_streaming.stream(
        system_prompt,
        openai_config,
        messages=messages,
        list_tools=mock_list_tools,
        call_tool=mock_call_tool,
    ):
        received_chunks.append(chunk)

    mock_list_tools.assert_awaited_once()
    assert mock_call_tool.call_count == 1, (
        f"Expected call_tool to be awaited once, but was awaited {mock_call_tool.await_count} times"
    )

    assert mock_client.chat.completions.create.call_count == 2, (
        f"Expected completions.create to be called twice, but was called {mock_client.chat.completions.create.await_count} times"
    )
