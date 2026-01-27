import json
from typing import Callable


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
        return "\n".join(
            f"`{tool}`: {self.tools[tool]['description']}" for tool in self.tools
        )
