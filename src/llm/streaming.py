import asyncio
import json
from dataclasses import dataclass, field
from typing import Annotated, Any, AsyncGenerator, Callable, Coroutine

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from src.mcp.utils import openai_func_def_from

from mcp.types import CallToolResult, ListToolsResult

from .config import OpenAIConfig


@dataclass(slots=True)
class OpenAIStreaming:
    client: AsyncOpenAI
    _call_tool: Callable[
        [Annotated[str, "tool_name"], dict, str], Coroutine[Any, Any, CallToolResult]
    ] = field(init=False)
    _list_tools: Callable[[], Coroutine[Any, Any, ListToolsResult]] = field(init=False)

    async def stream(
        self,
        system_prompt: str,
        config: OpenAIConfig,
        max_recursion: int = 10,
        messages: list[ChatCompletionMessageParam] = None,
        call_tool: Callable = None,
        list_tools: Callable = None,
    ) -> AsyncGenerator[str | dict, None]:
        """
        Stream responses from the model, handling both regular text and tool calls.

        Args:
            messages: List of chat messages to send to the model
            system_prompt: System prompt to guide model behavior
            openai_config: Optional configuration for this specific request
            max_recursion: Maximum number of recursive tool calls allowed

        Yields:
            Either string content or tool response dictionaries
        """
        tools = []

        if list_tools and call_tool:
            self._list_tools = list_tools
            self._call_tool = call_tool

            resp: ListToolsResult = await self._list_tools()
            tools = [openai_func_def_from(tool) for tool in resp.tools]

        # Ensure system prompt is the first message
        if not messages:
            messages = [{"role": "system", "content": system_prompt}]

        elif messages[0].get("role") != "system":
            messages = [{"role": "system", "content": system_prompt}, *messages]

        elif messages[0].get("content") != system_prompt:
            messages[0]["content"] = system_prompt

        # If no tools are available, use basic streaming
        if not tools:
            response = await self.client.chat.completions.create(
                messages=messages,
                model=config.model,
                stream=True,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            )
            async for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
            return

        # Stream with function calling enabled
        async for chunk in self._process_stream(
            messages, tools, config=config, max_recursion=max_recursion
        ):
            yield chunk

    async def _process_stream(
        self,
        messages: list[ChatCompletionMessageParam],
        tools: list[dict],
        config: OpenAIConfig,
        recursion_depth: int = 0,
        max_recursion: int = 10,
    ) -> AsyncGenerator[str | dict, None]:
        """
        Process a stream of responses from the model.

        Args:
            messages: List of messages to send to the model
            tools: List of available tool definitions
            config: OpenAI configuration for this request
            recursion_depth: Current depth of tool call recursion
            max_recursion: Maximum allowed recursion depth

        Yields:
            Either string content or tool response dictionaries
        """
        if recursion_depth >= max_recursion:
            yield json.dumps({"error": "Maximum tool call recursion depth exceeded"})
            return

        response = await self.client.chat.completions.create(
            messages=messages,
            model=config.model,
            stream=True,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            tools=tools,
            tool_choice="auto",
        )

        tool_calls_store: dict[str, dict] = {}
        last_call_id: str = None  # Tracks the most recent call ID

        # Process each chunk in the stream
        async for chunk in response:
            delta = chunk.choices[0].delta
            finish_reason = chunk.choices[0].finish_reason

            # 1) Stream normal content if any
            if delta.content:
                yield delta.content

            # 2) Handle partial tool calls
            if delta.tool_calls:
                for tool_call_delta in delta.tool_calls:
                    call_id = tool_call_delta.id

                    # A) If chunk has a new ID (non-null), start or retrieve an entry
                    if call_id:
                        last_call_id = call_id
                        if call_id not in tool_calls_store:
                            tool_calls_store[call_id] = {
                                "id": call_id,
                                "function": {"name": "", "arguments": ""},
                            }
                    else:
                        # B) If chunk has id=None, assume it belongs to the last known ID
                        if last_call_id is None:
                            # We have no known call => skip or handle error
                            continue
                        call_id = last_call_id

                    # Safely append name/arguments to tool_calls_store
                    if tool_call_delta.function.name:
                        tool_calls_store[call_id]["function"]["name"] = (
                            tool_call_delta.function.name
                        )

                    if tool_call_delta.function.arguments:
                        tool_calls_store[call_id]["function"]["arguments"] += (
                            tool_call_delta.function.arguments
                        )

            # If the model signals that tool calls are needed, process them
            if finish_reason == "tool_calls" and tool_calls_store:
                # Prepare all tool calls for execution
                tool_call_tasks = []
                tool_call_messages = []

                for tool_call in tool_calls_store.values():
                    tool_name: str = tool_call["function"]["name"]
                    tool_args: dict = tool_call["function"]["arguments"]

                    # Add tool call to message history
                    tool_call_messages.append(
                        {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": tool_call["id"],
                                    "type": "function",
                                    "function": {
                                        "name": tool_name,
                                        "arguments": tool_args,
                                    },
                                }
                            ],
                        }
                    )

                    # Execute tool
                    tool_call_tasks.append(
                        self._call_tool(
                            tool_name=tool_name,
                            tool_args=json.loads(tool_args),
                            tool_id=tool_call["id"],
                        )
                    )

                # Add all tool calls to message history
                messages.extend(tool_call_messages)

                # Execute all tool calls in parallel
                results: list[tuple[str, str, CallToolResult]] = await asyncio.gather(
                    *tool_call_tasks
                )

                # Add tool results to messages
                for tool_name, tool_call_id, result in results:
                    if result:
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "name": tool_name,
                                "content": result.content[0].text,
                            }
                        )

                # Clear the tool_calls_store for the next iteration
                tool_calls_store.clear()
                last_call_id = None

                # Recursively process the updated messages
                async for chunk in self._process_stream(
                    messages,
                    tools,
                    config=config,
                    recursion_depth=recursion_depth + 1,
                    max_recursion=max_recursion,
                ):
                    yield chunk

        # Handle cases where the stream ends without tool calls
        if finish_reason is None and not tool_calls_store:
            return
