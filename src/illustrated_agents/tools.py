import json
import inspect
import sys
import asyncio

from pathlib import Path
from typing import Callable
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import illustrated_agents
from illustrated_agents.llm import Response

SERVER_PATH = str(Path(illustrated_agents.__file__).parent / "chapters" / "ch5_mcp_server.py")


# Convert specific types to string descriptions
TYPE_MAP = {str: "string", int: "integer", float: "number", bool: "boolean", list: "array", dict: "object"}


def tool_to_schema(function) -> dict:
    """Convert a Python function to an OpenAI-style tool schema."""
    signature = inspect.signature(function)

    # Extract meatadata
    properties, required = {}, []
    for name, parameter in signature.parameters.items():
        properties[name] = {"type": TYPE_MAP.get(parameter.annotation, "string")}
        if parameter.default is inspect.Parameter.empty:
            required.append(name)

    # Fill schema
    schema = {
        "type": "function",
        "function": {
            "name": function.__name__,
            "description": inspect.getdoc(function),
            "parameters": {"type": "object", "properties": properties, "required": required},
        },
    }

    return schema


class Tools:
    """Tool registry for the Agent."""

    def __init__(self, requires_approval: list[str] = []):
        """Initialize Tools

        Arguments:
            requires_approval: A list of tool names that require human approval
        """
        self.registry = {}
        self.requires_approval = requires_approval

    def add_tool(self, name: str, func: Callable, description: str = ""):
        """Register a tool that the Agent can use.

        Arguments:
            name: The name of the tool.
            func: The function implementing the tool.
            description: A description of the tool.
        """
        self.registry[name] = {"function": func, "description": description}

    @property
    def descriptions(self):
        """Get descriptions of all registered tools."""
        return "\n".join(f"`{tool}`: {self.registry[tool]['description']}" for tool in self.registry)

    @property
    def prompt(self):
        return f"""
# Tools

If needed, you can only use the following tools to assist you in completing tasks:

{self.descriptions}

To use a tool, respond with JSON: {{"tool": "name", "kwargs": {{"param": "value"}}}}
"""

    def has_tool_call(self, response: Response) -> bool:
        """Check whether there is a tool call in `text`."""
        return '"tool":' in response.content or '"tool:"' in response.content

    def parse_tool_call(self, response: Response) -> dict:
        """Parse a JSON tool call from text."""
        text = response.content
        start, end = text.find("{"), text.rfind("}") + 1
        tool_call = json.loads(text[start:end])
        return tool_call

    def run_tool(self, tool_call: dict) -> any:
        """Run a registered tool.

        Arguments:
            tool_call: A parsed tool call dict with "tool" and "kwargs" keys.
        """
        name, kwargs = tool_call["tool"], tool_call.get("kwargs", {})

        # Human-in-the-loop: ask before running dangerous tools
        if name in self.registry and name in self.requires_approval:
            response = input(f"Allow {name}? [y/N] ").strip().lower()
            if response not in ("y", "yes"):
                return f"Tool '{name}' was denied by the user."

        # Handle registered tools
        if name in self.registry:
            tool_func = self.registry[name]["function"]
            return tool_func(**kwargs)

        return f"Tool '{name}' not found."

    @property
    def schemas(self):
        """Used only for native tool-calling."""
        return None


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


class NativeTools(Tools):
    """Tool registry using native function calling."""

    @property
    def schemas(self) -> list:
        """Return tool functions for native function calling."""
        return [tool_to_schema(tool["function"]) for tool in self.registry.values()]

    @property
    def prompt(self) -> str:
        """Empty because we don't need a prompt for native tool calling"""
        return ""

    def has_tool_call(self, response) -> bool:
        """Check whether the tool call is not empty."""
        return response.tool_call is not None

    def parse_tool_call(self, response) -> dict:
        """Parse a tool call."""
        args = response.tool_call["function"]["arguments"]
        if isinstance(args, str):
            args = json.loads(args)
        return {"tool": response.tool_call["function"]["name"], "kwargs": args}
