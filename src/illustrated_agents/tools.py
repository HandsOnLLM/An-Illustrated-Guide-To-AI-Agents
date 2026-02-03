import json
from typing import Callable
import sys
import asyncio
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import illustrated_agents
import nest_asyncio

nest_asyncio.apply()

SERVER_PATH = str(Path(illustrated_agents.__file__).parent / "chapters" / "ch5_mcp_server.py")


class Tools:
    """Tool registry for the Agent."""

    def __init__(self):
        self.tools = {}

    def add_tool(self, name: str, func: Callable, description: str):
        """Register a tool that the agent can use.

        Arguments:
            name: The name of the tool.
            func: The function implementing the tool.
            description: A description of the tool.
        """
        self.tools[name] = {"function": func, "description": description}

    def run_tool(self, tool_call: dict) -> any:
        """Run a registered tool.

        Arguments:
            tool_call: A parsed tool call dict with "tool" and "args" keys.
        """
        name, args = tool_call["tool"], tool_call.get("args", [])

        # Handle registered tools
        if name in self.tools:
            tool_func = self.tools[name]["function"]
            return tool_func(*args)

        # Handle intermediate_answer (allows LLM to respond without a real tool)
        if name == "intermediate_answer":
            return args

        return f"Tool '{name}' not found."

    def is_tool_call(self, text: str) -> bool:
        """Check whether there is a tool call in `text`."""
        return '"tool":' in text or '"tool:"' in text

    def parse_tool_call(self, text: str) -> dict:
        """Parse a JSON tool call from text."""
        start, end = text.find("{"), text.rfind("}") + 1
        tool_call = json.loads(text[start:end])
        return tool_call

    @property
    def prompt(self):
        return f"""
# Tools

If needed, you can only use the following tools to assist you in completing tasks:

{self.descriptions}

To use a tool, respond with JSON: {{"tool": "name", "args": [...]}}
"""

    @property
    def descriptions(self):
        """Get descriptions of all registered tools."""
        return "\n".join(f"`{tool}`: {self.tools[tool]['description']}" for tool in self.tools)


class MCPTools(Tools):
    """MCP-based tool registry that extends Tools."""

    def __init__(self):
        super().__init__()
        self._load_mcp_tools()

    def _get_server_params(self):
        return StdioServerParameters(command=sys.executable, args=[SERVER_PATH])

    def _load_mcp_tools(self):
        """Fetch tools from MCP server and register them."""

        # Fetch the list of tools from the MCP server
        async def fetch():
            async with stdio_client(self._get_server_params(), errlog=None) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    return tools.tools

        mcp_tools = asyncio.run(fetch())

        # Register each MCP tool using parent's add_tool
        for tool in mcp_tools:
            self.add_tool(
                name=tool.name,
                func=self._make_tool_caller(tool.name, tool.inputSchema),
                description=tool.description,
            )

    def _make_tool_caller(self, name: str, schema: dict):
        """Create a callable that invokes the MCP tool."""
        param_names = list(schema.get("properties", {}).keys())

        def caller(*args):
            # Convert positional args to named args since MCP expects named args and
            # the original Tools interface uses positional args.
            named_args = dict(zip(param_names, args))
            return asyncio.run(self._call_tool(name, named_args))

        return caller

    async def _call_tool(self, name: str, args: dict) -> str:
        """Call a tool on the MCP server."""
        async with stdio_client(self._get_server_params(), errlog=None) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(name, args)
                return result.content[0].text
