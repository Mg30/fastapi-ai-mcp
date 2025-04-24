import asyncio
import json
from dataclasses import dataclass, field
from typing import Annotated, Any, Callable, Coroutine, List, Optional, Union

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from src.mcp.utils import openai_func_def_from

from mcp.types import CallToolResult, ListToolsResult

from .config import OpenAIConfig


@dataclass
class OpenAI:
    client: AsyncOpenAI
    _call_tool: Callable[
        [Annotated[str, "tool_name"], dict, str], Coroutine[Any, Any, CallToolResult]
    ] = field(init=False)
    _list_tools: Callable[[], Coroutine[Any, Any, ListToolsResult]] = field(init=False)

    async def call(
        self,
        system_prompt: str,
        config: OpenAIConfig,
        max_recursion: int = 10,
        messages: Optional[List[ChatCompletionMessageParam]] = None,
        call_tool: Callable[
            [Annotated[str, "tool_name"], dict, str],
            Coroutine[Any, Any, CallToolResult],
        ] = None,
        list_tools: Callable[[], Coroutine[Any, Any, ListToolsResult]] = None,
    ) -> Union[str, dict]:
        """
        Generate a complete response from the model without streaming, handling both regular text and tool calls.

        Args:
            system_prompt: System prompt to guide model behavior.
            config: Configuration for the OpenAI request.
            max_recursion: Maximum number of recursive tool calls allowed.
            messages: Optional list of chat messages to send to the model.

        Returns:
            The complete response as a string or a dictionary containing error information.
        """
        # Ensure system prompt is the first message
        if not messages:
            messages = [{"role": "system", "content": system_prompt}]
        elif messages[0].get("role") != "system":
            messages = [{"role": "system", "content": system_prompt}, *messages]
        elif messages[0].get("content") != system_prompt:
            messages[0]["content"] = system_prompt

        tools = []

        if list_tools and call_tool:
            self._call_tool = call_tool
            self._list_tools = list_tools
            resp = await self._list_tools()
            tools = [openai_func_def_from(tool) for tool in resp.tools]

        # If no tools are available, perform a single request
        if not tools:
            try:
                response = await self.client.chat.completions.create(
                    messages=messages,
                    model=config.model,
                    stream=False,  # Non-streaming
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                )
                # Extract and return the content
                content = response.choices[0].message.get("content", "")
                return content
            except Exception as e:
                return {"error": f"OpenAI API error: {str(e)}"}

        recursion_depth = 1
        final_response = await self.process_messages(
            messages,
            tools=tools,
            config=config,
            recursion_depth=recursion_depth,
            max_recursion=max_recursion,
        )
        return final_response

    async def process_messages(
        self,
        messages: List[ChatCompletionMessageParam],
        recursion_depth: int,
        config: OpenAIConfig,
        tools: list[dict],
        max_recursion: int = 5,
    ) -> str | dict:
        if recursion_depth > max_recursion:
            return {"error": "Maximum tool call recursion depth exceeded"}

        try:
            # Make a chat completion request with function calling enabled
            response = await self.client.chat.completions.create(
                messages=messages,
                model=config.model,
                stream=False,  # Non-streaming
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                tools=tools,
                tool_choice="auto",
            )
        except Exception as e:
            return {"error": f"OpenAI API error: {str(e)}"}

        message = response.choices[0].message

        if not message.tool_calls:
            return message

        messages.append(message)

        tool_call_tasks = []

        for tool_call in message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            tool_call_tasks.append(
                self._call_tool(
                    tool_name=name,
                    tool_args=args,
                    tool_id=tool_call.id,
                )
            )

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

        return await self.process_messages(
            messages=messages,
            recursion_depth=recursion_depth + 1,
            config=config,
            tools=tools,
        )
