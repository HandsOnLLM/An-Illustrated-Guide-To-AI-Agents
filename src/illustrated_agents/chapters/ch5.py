import json
from typing import Callable

from illustrated_agents.tools import MCPTools
from illustrated_agents.utils import DiffViewer, CodeAnnotator, ChapterOverview
from illustrated_agents.chapters import ch4
from illustrated_agents.chapters.ch2 import LLM, Response
from illustrated_agents.chapters.ch4 import Memory


class Tools:
    """Tool registry for the Agent."""

    def __init__(self):
        self.registry = {}

    def add_tool(self, name: str, func: Callable, description: str = ""):
        """Register a tool that the Agent can use.

        Arguments:
            name: The name of the tool.
            func: The function implementing the tool.
            description: A description of the tool.
        """
        self.registry[name] = {"function": func, "description": description}

    @property
    def descriptions(self) -> str:
        """Get descriptions of all registered tools."""
        return "\n".join(f"`{tool}`: {self.registry[tool]['description']}" for tool in self.registry)

    @property
    def prompt(self) -> str:
        return f"""
# Tools

If needed, you can only use the following tools to assist you in completing tasks:

{self.descriptions}

To use a tool, respond with JSON: {{"tool": "name", "kwargs": {{"param": "value"}}}}
"""

    def parse(self, response: Response) -> Response:
        """Parse a JSON tool call from text."""
        text = response.content

        if '"tool":' in text or '"tool:"' in text:
            start, end = text.find("{"), text.rfind("}") + 1
            tool_call = json.loads(text[start:end])

            # Add the parsed tool call to the response
            return Response(
                content=response.content,
                reasoning=response.reasoning,
                tool_call=tool_call,
            )

        return response

    def execute(self, response: Response) -> any:
        """Run a registered tool.

        Arguments:
            tool_call: A parsed tool call dict with "tool" and "kwargs" keys.
        """
        tool_call = response.tool_call
        name, kwargs = tool_call["tool"], tool_call.get("kwargs", {})

        # Handle registered tools
        if name in self.registry:
            tool_func = self.registry[name]["function"]
            return tool_func(**kwargs)

        return f"Tool '{name}' not found."

    def observation(self, result):
        """Return the observation as a user."""
        return "user", f"OBSERVATION: {result}"

    def is_done(self, response: Response) -> bool:
        """The `TinyAgent` is done if there is no tool call."""
        return not response.tool_call

    @property
    def schemas(self):
        """Used only for native tool-calling."""
        return None


class TinyAgent:
    """A minimal, modular, and educational agent framework."""

    def __init__(self, llm: LLM, memory: Memory, tools: Tools):
        self.llm = llm
        self.memory = memory
        self.tools = tools
        self.planner = None  # Chapter 6: Add Planning
        self.skills = None  # Chapter 6: Add Skills

        # Build system prompt with all components
        system_prompt = "You are a helpful assistant.\n\n"
        system_prompt += self.tools.prompt
        self.memory.add("system", system_prompt)

    def run(self, task: str) -> str:
        """Run the agent on a task."""
        self.memory.add("user", task)

        return self._step()

    def _step(self) -> str:
        """Perform a single step."""
        # THOUGHT: Generate response and add to memory
        response = self.llm.generate(self.memory.get_messages())
        self.memory.add("assistant", response.content)

        # Tool parsing
        response = self.tools.parse(response)

        # ANSWER: Stopping mechanism
        if self.tools.is_done(response):
            return response.content

        return self._execute_action(response)

    def _execute_action(self, response: Response) -> None:
        """Execute a tool action."""

        # ACTION: execute tools
        result = self.tools.execute(response)

        # OBSERVATION: add tool results to memory and display
        role, observation = self.tools.observation(result)
        self.memory.add(role, observation)

        return observation


what_we_built = ChapterOverview(
    [
        ("agent.py", "updated", "Added `Tools`!"),
        ("llm.py", None, ""),
        ("memory.py", None, ""),
        ("toolbox.py", "new", "This file tracks all tools that were created for easy reference."),
        ("tools.py", "new", "Created a tool registry, parsing, and execution class."),
    ]
)

what_we_built_mcp = ChapterOverview(
    [
        ("agent.py", None, ""),
        ("llm.py", None, ""),
        ("memory.py", None, ""),
        ("toolbox.py", None, ""),
        ("tools.py", "updated", "Added `MCPTools` to use Model Context Protocol (MCP)."),
    ]
)


tinyagents_diff = DiffViewer(ch4.TinyAgent, TinyAgent, "ch4.TinyAgent", "ch5.TinyAgent")


agent_init_annotated = CodeAnnotator(
    TinyAgent.__init__,
    annotations={
        (9, 12): """
A system prompt is constructed that includes the base instruction and the tool descriptions. 
This system prompt is added to memory at initialization so that the LLM is aware of the tools from the very beginning.
""",
    },
)

agent_step_annotated = CodeAnnotator(
    TinyAgent._step,
    annotations={
        (7, 9): """
After generating a response, we check if the response contains a tool call. If it does, we execute the tool action instead of returning the LLM's response directly.
""",
    },
)

agent_execute_action_annotated = CodeAnnotator(
    TinyAgent._execute_action,
    annotations={
        3: "(1) The tool call is parsed to extract the tool name and arguments.",
        6: "(2) the tool is executed using the `Tools` class which looks up the tool in the registry and calls it.",
        8: "(3) The result of the tool execution is stored as an observation in memory.",
    },
)


parse_tool_annotated = CodeAnnotator(
    Tools.parse,
    annotations={
        6: "We expect a simple JSON string and only need to extract within {} brackets.",
        (10, 14): "The parsed tool call is added to the `Response` object for later use in execution.",
        16: "If no tool call is found, the original response is returned.",
    },
)

execute_tool_annotated = CodeAnnotator(
    Tools.execute,
    annotations={
        (7, 8): "The tool name and possible arguments are extracted from the parsed tool call.",
        (12, 13): "Tools are looked up in the registry and executed with the provided arguments.",
        15: "If the tool is not found, an error message is returned which can be saved in the Agent's memory as feedback.",
        16: "",
    },
)

observation_tool_annotated = CodeAnnotator(
    Tools.observation,
    annotations={
        3: "The observation is returned as a user message. This way, the result of the tool execution can be processed by the LLM in the next step.",
    },
)

done_tool_annotated = CodeAnnotator(
    Tools.is_done,
    annotations={
        3: "A simple stopping mechanism is implemented where the agent is considered done if there is no tool call in the response.",
    },
)


run_mcp_tool_annotated = CodeAnnotator(
    MCPTools,
    annotations={
        6: "This is the main function for loading the tools.",
        9: "This the the path to your MCP server.",
        (
            15,
            20,
        ): """The tools are retrieved from the MCP Server using `list_tools()`. The `list_tools()` function is a 
standardized way to query an MCP server for its available tools. This will always return a list of tool metadata, including 
tool names, descriptions, and parameter specifications.""",
        (
            25,
            30,
        ): """The listed tools are added to the registry that we defined previously in Chapter 5 using the `Tools` class. 
Here, the `_make_tool_caller` creates a callable function for each tool that knows how to call the MCP server with the correct parameters.""",
        (
            42,
            46,
        ): """As before, the MCP Server is called and the corresponding tool, together with their arguments, are called using 
the MCP Server. The execution is done with `session.call_tool` which again is a standardized function according to the MCP Protocol.""",
    },
)
