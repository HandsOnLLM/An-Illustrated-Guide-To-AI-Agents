import sys
import asyncio
import urllib.request

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.server.fastmcp import FastMCP

from illustrated_agents.tools import Tools


# --- MCP server (runs when this module is executed as __main__) ---

server = FastMCP("file_reader")


@server.tool()
def read_markdown(path: str) -> str:
    """Read the content of a markdown file.

    Args:
        path (str): The path to the markdown file.
    """
    with urllib.request.urlopen(path) as resp:
        return resp.read().decode()


# --- MCP client (used by TinyAgent) ---


class MCPTools(Tools):
    """MCP-based tool registry that extends Tools."""

    def __init__(self):
        super().__init__()
        self._load_mcp_tools()

    def _get_server_params(self):
        return StdioServerParameters(
            command=sys.executable,
            args=["-m", "illustrated_agents.mcp"],
        )

    def _load_mcp_tools(self):
        """Fetch tools from MCP server and register them."""

        # Fetch the list of tools from the MCP server
        async def fetch():
            async with stdio_client(self._get_server_params(), errlog=None) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    return tools.registry

        mcp_tools = asyncio.run(fetch())

        # Register each MCP tool using parent's add_tool
        for tool in mcp_tools:
            self.add_tool(
                name=tool.name,
                func=self._make_tool_caller(tool.name),
                description=tool.description,
            )

    def _make_tool_caller(self, name: str):
        """Create a callable that invokes the MCP tool."""

        def caller(**kwargs):
            return asyncio.run(self._call_tool(name, kwargs))

        return caller

    async def _call_tool(self, name: str, args: dict) -> str:
        """Call a tool on the MCP server."""
        async with stdio_client(self._get_server_params(), errlog=None) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(name, args)
                return result.content[0].text


def main():
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
