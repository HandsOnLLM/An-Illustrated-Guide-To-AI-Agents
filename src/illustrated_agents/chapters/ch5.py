import inspect
import json
import yaml
from pathlib import Path
from typing import Any, Callable

from illustrated_agents.utils import DiffViewer, CodeAnnotator, ChapterOverview
from illustrated_agents.chapters import ch4
from illustrated_agents.chapters.ch2 import LLM, Response, Trajectory
from illustrated_agents.chapters.ch4 import Memory


# Convert specific types to string descriptions
TYPE_MAP = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}


def tool_to_schema(function: Callable) -> dict:
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
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }

    return schema


class Tools:
    """Tool registry for the Agent."""

    def __init__(self, requires_approval: list[str] = []):
        """Initialize and select tools that require approval before execution."""
        self.registry = {}
        self.requires_approval = requires_approval

    def add_tool(self, name: str, func: Callable, description: str = "") -> None:
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
        return "\n".join(
            f"`{tool}`: {self.registry[tool]['description']}"
            for tool in self.registry
        )

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

    def execute(self, response: Response) -> Any:
        """Run a registered tool.

        Arguments:
            tool_call: A parsed tool call dict with "tool" and "kwargs" keys.
        """
        tool_call = response.tool_call
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

    def observation(self, result: str) -> tuple[str, str]:
        """Return the observation as a user."""
        return "user", f"OBSERVATION: {result}"

    def is_done(self, response: Response) -> bool:
        """The `TinyAgent`'s stopping mechanism."""
        if not response.tool_call:
            return True
        if response.tool_call["tool"] == "final_answer":
            response.content = response.tool_call.get("kwargs", "")
            return True
        return False

    @property
    def schemas(self) -> None:
        """Used only for native tool-calling."""
        return None


class NativeTools(Tools):
    """Tool registry using native function calling."""

    @property
    def schemas(self) -> list[dict]:
        """Return tool functions for native function calling."""
        return [
            tool_to_schema(tool["function"]) for tool in self.registry.values()
        ]

    @property
    def prompt(self) -> str:
        """Empty because we don't need a prompt for native tool calling"""
        return ""

    def parse(self, response: Response) -> Response:
        """Parse a tool call."""
        # If there's no tool call, return the response as is
        if not response.tool_call:
            return response

        # Extract the tool name and arguments from the tool call
        args = response.tool_call["function"]["arguments"]
        if isinstance(args, str):
            args = json.loads(args)
        tool_call = {
            "tool": response.tool_call["function"]["name"],
            "kwargs": args,
        }

        # Add the parsed tool call to the response
        return Response(
            content=response.content,
            reasoning=response.reasoning,
            tool_call=tool_call,
        )

    def observation(self, result: str) -> tuple[str, str]:
        """Native tool results use the 'tool' role."""
        return "tool", str(result)

    def is_done(self, response: Response) -> bool:
        """No tool call means the `TinyAgent` is done."""
        return not response.tool_call


class Skills(NativeTools):
    """A `Tools` and `Skills` registry

    Skills are recipes. When you activate one, you get instructions
    in return on how to approach a given task. Although it is not
    a tool in the same way a calculator is one, we can still approach
    it as such since the Agent has to decide when to activate it.

    The skills are loaded progressively. As such, the name and description are
    available in the system prompt, but the full instructions are only injected
    when the agent **activates** a skill (uses it as a tool).
    """

    def add_skill(self, path: str) -> None:
        """Load a SKILL.md file and register it as a callable tool."""
        content = Path(path).read_text(encoding="utf-8")

        # Split on YAML delimiters and extract the frontmatter and instructions
        parts = content.split("---", 2)
        frontmatter = yaml.safe_load(parts[1])
        name = frontmatter["name"]
        description = frontmatter["description"]
        instructions = parts[2].strip()

        # Register the skill
        def skill(**kwargs) -> str:
            return instructions

        skill.__name__ = name
        skill.__doc__ = f"A skill that when activated provides the following context: '{description}'"
        skill.__signature__ = (
            inspect.Signature()
        )  # schema sees no params; lambda still tolerates any
        self.add_tool(name, skill, skill.__doc__)

    @property
    def prompt(self) -> str:
        return """You have specialized skills available. To use a skill,
call it like a tool by referencing their name.

The skill will provide detailed instructions for completing the task."""


class TinyAgent:
    """A minimal, modular, and educational agent framework."""

    def __init__(self, llm: LLM, memory: Memory, tools: Tools):
        self.llm = llm
        self.memory = memory
        self.tools = tools
        self.planner = None  # Chapter 6: Add Planning

        self.trajectory = Trajectory()

        # Build system prompt with all components
        system_prompt = "You are a helpful assistant.\n\n"
        system_prompt += self.tools.prompt
        self.memory.add("system", system_prompt)

    def run(self, task: str) -> str:
        """Run the agent on a task."""
        self.memory.add("user", task)
        self.trajectory.initialize(task)

        return self._step()

    def _step(self) -> str:
        """Perform a single step."""
        # THOUGHT: Generate response and add to memory
        response = self.llm.generate(
            self.memory.get_messages(), tools=self.tools.schemas
        )
        self.memory.add(
            "assistant", response.content, tool_call=response.tool_call
        )

        # Tool parsing
        response = self.tools.parse(response)

        # ANSWER: Stopping mechanism
        if self.tools.is_done(response):
            self.trajectory.add(response)
            return response.content

        return self._execute_action(response)

    def _execute_action(self, response: Response) -> str:
        """Execute a tool action."""

        # ACTION: execute tools
        result = self.tools.execute(response)

        # OBSERVATION: add tool results to memory and display
        role, observation = self.tools.observation(result)
        self.memory.add(role, observation)
        self.trajectory.add(response, observation)

        return observation


what_we_built = ChapterOverview(
    [
        ("agent.py", "updated", "Added `Tools`!"),
        ("llm.py", None, ""),
        ("memory.py", None, ""),
        (
            "toolbox.py",
            "new",
            "This file tracks all tools that were created for easy reference.",
        ),
        (
            "tools.py",
            "new",
            "Created a tool registry, parsing, and execution class.",
        ),
        ("trajectory.py", None, ""),
    ]
)

what_we_built_native = ChapterOverview(
    [
        (
            "agent.py",
            "updated",
            "Updated `TinyAgent` to handle native tool calling.",
        ),
        (
            "llm.py",
            "updated",
            "Extract tool calls from LLM response metadata instead of text parsing.",
        ),
        (
            "memory.py",
            "updated",
            "Track tool calling and observations in memory.",
        ),
        ("toolbox.py", None, ""),
        ("tools.py", "updated", "Create `NativeTools` for native tool calling."),
        ("trajectory.py", None, ""),
    ]
)

what_we_built_skills = ChapterOverview(
    [
        ("agent.py", None, ""),
        ("llm.py", None, ""),
        ("memory.py", None, ""),
        ("toolbox.py", None, ""),
        ("tools.py", "updated", "Added `Skills` using both Tools and Skills."),
        ("trajectory.py", None, ""),
    ]
)


tinyagents_diff = DiffViewer(
    ch4.TinyAgent, TinyAgent, "ch4.TinyAgent", "ch5.TinyAgent"
)


agent_init_annotated = CodeAnnotator(
    TinyAgent.__init__,
    annotations={
        (10, 12): """
A system prompt is constructed that includes the base instruction and the tool descriptions. 
This system prompt is added to memory at initialization so that the LLM is aware of the tools from the very beginning.
""",
    },
)

agent_step_annotated = CodeAnnotator(
    TinyAgent._step,
    annotations={
        8: "The tool call is parsed to extract the tool name and arguments.",
        (11, 13): """
After generating a response, we check if the response contains a tool call. If it does, we execute the tool action instead of returning the LLM's response directly.
""",
    },
)

agent_execute_action_annotated = CodeAnnotator(
    TinyAgent._execute_action,
    annotations={
        5: "(1) the tool is executed using the `Tools` class which looks up the tool in the registry and calls it.",
        9: "(2) The result of the tool execution is stored as an observation in memory.",
        10: "(3) The trajectory is updated with the tool call and observation.",
    },
)


parse_tool_annotated = CodeAnnotator(
    Tools.parse,
    annotations={
        6: "We expect a simple JSON string and only need to extract within {} brackets.",
        (
            10,
            14,
        ): "The parsed tool call is added to the `Response` object for later use in execution.",
        16: "If no tool call is found, the original response is returned.",
    },
)

execute_tool_annotated = CodeAnnotator(
    Tools.execute,
    annotations={
        (
            7,
            8,
        ): "The tool name and possible arguments are extracted from the parsed tool call.",
        (
            11,
            14,
        ): "If the tool requires approval, we ask the user for confirmation before executing it. More on this in Chapter 10.",
        (
            17,
            19,
        ): "Tools are looked up in the registry and executed with the provided arguments.",
        21: "Returns an error message to the LLM if the tool is not found..",
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
        (3, 4): "Stops when there is no tool call.",
        (
            6,
            7,
        ): "Stops when the `final_answer` tool is called, which allows the agent to signal that it has completed the task and provide a final answer. Only used in Chapter 6!)",
    },
)
