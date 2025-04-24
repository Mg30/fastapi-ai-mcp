# /// script
# requires-python = ">=3.12"
# dependencies = ["mcp[cli]"]
# ///


from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Echo")


@mcp.resource("echo://{message}")
def echo_resource(message: str) -> str:
    """Echo a message as a resource"""
    return f"Resource echo: {message}"


@mcp.tool()
def echo_tool(message: str) -> dict:
    """Echo a message as a tool"""
    return {"test": message}


if __name__ == "__main__":
    mcp.run()
