from mcp import ClientSession, StdioServerParameters, Tool, stdio_client
from mcp.types import CallToolResult


def call_tool_factory(server_params: StdioServerParameters):
    async def call_tool(
        tool_name: str, tool_args: dict, tool_id: str
    ) -> tuple[str, str, CallToolResult]:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                res = await session.call_tool(tool_name, arguments=tool_args)
        return tool_name, tool_id, res

    return call_tool


def list_tools_factory(server_params: StdioServerParameters):
    async def list_tools():
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
        return tools

    return list_tools


def openai_func_def_from(tool: Tool) -> dict:
    """Transform a mcp Tool to an open ai function call"""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": {**tool.inputSchema, "additionalProperties": False},
            "strict": True,
        },
    }
