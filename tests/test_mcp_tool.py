from src.mcp.utils import openai_func_def_from

from mcp import Tool


def test_mcp_tool_to_openai_def():
    tool = Tool(
        name="echo_tool",
        description="Echo a message as a tool",
        inputSchema={
            "properties": {"message": {"title": "Message", "type": "string"}},
            "required": ["message"],
            "title": "echo_toolArguments",
            "type": "object",
        },
    )

    res = openai_func_def_from(tool)
    assert res == {
        "type": "function",
        "function": {
            "name": "echo_tool",
            "description": "Echo a message as a tool",
            "parameters": {
                "properties": {"message": {"title": "Message", "type": "string"}},
                "required": ["message"],
                "title": "echo_toolArguments",
                "type": "object",
                "additionalProperties": False,
            },
            "strict": True,
        },
    }
