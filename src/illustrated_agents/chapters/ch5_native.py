import json
import inspect
import litellm
import ollama
from openai import OpenAI

from illustrated_agents.utils import CodeAnnotator, ChapterOverview, DiffViewer
from illustrated_agents.chapters.ch2 import Response, Backend
from illustrated_agents.chapters.ch5 import Tools
from illustrated_agents.chapters import ch2, ch5


# Convert specific types to string descriptions
TYPE_MAP = {str: "string", int: "integer", float: "number", bool: "boolean", list: "array", dict: "object"}


def function_to_dict(function) -> dict:
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


class LLM:
    def __init__(
        self,
        model: str,
        backend: Backend,
        api_key: str = "no_key_required",
        api_base: str = None,
        think: bool = False,
        **kwargs,
    ):
        """Initialize the LLM with the given model."""
        self.model = model
        self.backend = backend
        self.api_key = api_key
        self.api_base = api_base
        self.think = think
        self.kwargs = kwargs

        if self.backend == Backend.OPENAI:
            self.client = OpenAI(base_url=api_base, api_key=api_key)

    def generate(self, messages: list[dict], tools: list = None) -> Response:
        """Generate a response from the LLM given a list of messages."""

        # LiteLLM
        if self.backend == Backend.LITELLM:
            return self.litellm(messages, tools)

        # OpenAI API
        elif self.backend == Backend.OPENAI:
            return self.openai(messages, tools)

        # Ollama
        elif self.backend == Backend.OLLAMA:
            return self.ollama(messages, tools)

        else:
            raise ValueError(f"Unsupported backend: {self.backend}")

    def ollama(self, messages: list[dict], tools: list = None) -> Response:
        """Generate a response from Ollama."""
        response = ollama.chat(
            model=self.model,
            messages=messages,
            think=self.think,
            tools=tools,
            **self.kwargs,
        )

        # Format as Response dataclass
        message = response.message
        has_tool_call = hasattr(message, "tool_calls") and message.tool_calls
        tool_call = message.tool_calls[0].model_dump() if has_tool_call else None

        return Response(
            content=message.content,
            reasoning=getattr(message, "thinking", None),
            tool_call=tool_call,
        )

    def openai(self, messages: list[dict], tools: list = None) -> Response:
        """Generate a response from the OpenAI API."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools if tools else None,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}, "reasoning_effort": "none"}
            if not self.think
            else None,
            **self.kwargs,
        )

        # Format as Response dataclass
        message = response.choices[0].message
        has_tool_call = hasattr(message, "tool_calls") and message.tool_calls
        tool_call = message.tool_calls[0].model_dump() if has_tool_call else None

        return Response(
            content=message.content,
            reasoning=getattr(message, "reasoning_content", None) or getattr(message, "reasoning", None),
            tool_call=tool_call,
        )

    def litellm(self, messages: list[dict], tools: list = None) -> Response:
        """Generate a response from LiteLLM."""
        response = litellm.completion(
            model=self.model,
            messages=messages,
            api_base=self.api_base,
            api_key=self.api_key,
            tools=tools,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}, "reasoning_effort": "none"}
            if not self.think
            else None,
            **self.kwargs,
        )

        # Format as Response dataclass
        message = response.choices[0].message
        has_tool_call = hasattr(message, "tool_calls") and message.tool_calls
        tool_call = message.tool_calls[0].model_dump() if has_tool_call else None

        return Response(
            content=message.content,
            reasoning=getattr(message, "reasoning_content", None) or getattr(message, "reasoning", None),
            tool_call=tool_call,
        )


class Memory:
    """Simple memory module to store conversation history."""

    def __init__(self):
        self.messages = []

    def add(self, role: str, content: str, tool_call: dict = None):
        """Add a message to memory."""
        message = {"role": role, "content": content}

        # Tool call
        if tool_call:
            message["tool_calls"] = [tool_call]

        # Append message to memory
        self.messages.append(message)

    def get_messages(self) -> list[dict]:
        """Get all messages."""
        return self.messages


class NativeTools(Tools):
    """Tool registry using native function calling."""

    @property
    def tool_functions(self) -> list:
        """Return tool functions for native function calling."""
        return [tool["function"] for tool in self.registry.values()]

    @property
    def prompt(self) -> str:
        """Empty because we don't need a prompt for native tool calling"""
        return ""

    def has_tool_call(self, response) -> bool:
        """Check whether the response contains native tool calls."""
        return hasattr(response, "tool_calls") and response.tool_calls is not None

    def parse_tool_call(self, response) -> dict:
        """Parse a tool call."""
        tool_call = response.tool_calls[0]
        args = json.loads(tool_call["function"]["arguments"])
        return {"tool": tool_call["function"]["name"], "kwargs": args}


class TinyAgent:
    """A minimal, modular, and educational agent framework."""

    def __init__(self, llm: LLM, memory: Memory, tools: Tools):
        self.llm = llm
        self.memory = memory
        self.tools = tools
        self.planner = None  # Chapter 6: Add Planning
        self.reflector = None  # Chapter 6: Add Reflection
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
        # Generate response and add to memory
        response = self.llm.generate(self.memory.get_messages(), tools=self.tools.schemas)
        self.memory.add("assistant", response.content, tool_call=response.tool_call)

        # Tool parsing and execution
        if self.tools.has_tool_call(response):
            return self._execute_action(response)

        return response.content

    def _execute_action(self, response: Response) -> str | None:
        """Execute a tool action."""
        tool_call = self.tools.parse_tool_call(response)

        # Execute tool and extract the observation
        observation = self.tools.run_tool(tool_call)
        obs_prompt = f"OBSERVATION: {response.content} -> {observation}"

        # Native tool calling should get the role `tool`
        if self.tools.schemas:
            self.memory.add("tool", str(observation))
        else:
            self.memory.add("user", f"OBSERVATION: {observation}")

        return observation if self.tools.schemas else obs_prompt


what_we_built = ChapterOverview(
    [
        ("agent.py", "updated", "Added `NativeTools`!"),
        ("llm.py", None, ""),
        ("memory.py", None, ""),
        ("toolbox.py", "new", "This file tracks all tools that were created for easy reference."),
        ("tools.py", "new", "Created a tool registry, parsing, and execution class."),
    ]
)

llm_diff = DiffViewer(ch2.LLM.openai, LLM.openai, "ch2.LLM", "ch5.LLM")
tinyagents_diff = DiffViewer(ch5.TinyAgent, TinyAgent, "ch5.TinyAgent", "ch5_native.TinyAgent")

# tinyagents_diff = DiffViewer(ch4.TinyAgent, TinyAgent, "ch4.TinyAgent", "ch5.TinyAgent")


# agent_init_annotated = CodeAnnotator(
#     TinyAgent.__init__,
#     annotations={
#         (9, 12): """
# A system prompt is constructed that includes the base instruction and the tool descriptions.
# This system prompt is added to memory at initialization so that the LLM is aware of the tools from the very beginning.
# """,
#     },
# )

# agent_step_annotated = CodeAnnotator(
#     TinyAgent._step,
#     annotations={
#         (7, 9): """
# After generating a response, we check if the response contains a tool call. If it does, we execute the tool action instead of returning the LLM's response directly.
# """,
#     },
# )

# agent_execute_action_annotated = CodeAnnotator(
#     TinyAgent._execute_action,
#     annotations={
#         3: "(1) The tool call is parsed to extract the tool name and arguments.",
#         6: "(2) the tool is executed using the `Tools` class which looks up the tool in the registry and calls it.",
#         8: "(3) The result of the tool execution is stored as an observation in memory.",
#     },
# )


add_nativetool_annotated = CodeAnnotator(
    Tools.has_tool_call,
    annotations={
        3: """We check whether there is a tool call by seeing if `"tool":` appears in the text. If it does, we think there is a tool call. """
    },
)

parse_tool_annotated = CodeAnnotator(
    Tools.parse_tool_call,
    annotations={3: "We expect a simple JSON string and only need to extract within {} brackets."},
)

run_tool_annotated = CodeAnnotator(
    Tools.run_tool,
    annotations={
        7: "The tool name and possible arguments are extracted from the parsed tool call.",
        (11, 12): "Tools are looked up in the registry and executed with the provided arguments.",
    },
)
