import json
import inspect
from openai import OpenAI

from illustrated_agents.utils import ChapterOverview, DiffViewer
from illustrated_agents.chapters.ch2 import Response, Trajectory
from illustrated_agents.chapters.ch5 import Tools
from illustrated_agents.chapters import ch2, ch5


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


class LLM:
    def __init__(self, model: str, client: OpenAI, think: bool = False, **kwargs):
        """Initialize the LLM with the given model."""
        self.model = model
        self.client = client
        self.think = think
        self.kwargs = kwargs

    def generate(self, messages: list[dict], tools: list = None) -> Response:
        """Generate a response from the LLM given a list of messages."""
        # Enable/Disable thinking
        if self.think:
            extra_body = None
        else:
            extra_body = {"chat_template_kwargs": {"enable_thinking": False}, "reasoning_effort": "none"}

        # Generate a response
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools if tools else None,
            extra_body=extra_body,
            **self.kwargs,
        )

        # Extract message, tool_call, and metadata
        message = response.choices[0].message
        has_tool_call = hasattr(message, "tool_calls") and message.tool_calls
        tool_call = message.tool_calls[0].model_dump() if has_tool_call else None
        metadata = {
            "model": response.model,
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
        }

        # Format as Response dataclass
        return Response(
            content=message.content,
            reasoning=getattr(message, "reasoning_content", None) or getattr(message, "reasoning", None),
            tool_call=tool_call,
            metadata=metadata,
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
    def schemas(self) -> list:
        """Return tool functions for native function calling."""
        return [tool_to_schema(tool["function"]) for tool in self.registry.values()]

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
        tool_call = {"tool": response.tool_call["function"]["name"], "kwargs": args}

        # Add the parsed tool call to the response
        return Response(
            content=response.content,
            reasoning=response.reasoning,
            tool_call=tool_call,
        )

    def observation(self, result) -> tuple[str, str]:
        """Native tool results use the 'tool' role."""
        return "tool", str(result)

    def is_done(self, response: Response) -> bool:
        """No tool call means the `TinyAgent` is done."""
        return not response.tool_call


class TinyAgent:
    """A minimal, modular, and educational agent framework."""

    def __init__(self, llm: LLM, memory: Memory, tools: Tools):
        self.llm = llm
        self.memory = memory
        self.tools = tools
        self.planner = None  # Chapter 6: Add Planning
        self.skills = None  # Chapter 6: Add Skills

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
        response = self.llm.generate(self.memory.get_messages(), tools=self.tools.schemas)
        self.memory.add("assistant", response.content, tool_call=response.tool_call)

        # Tool parsing
        response = self.tools.parse(response)

        # ANSWER: Stopping mechanism
        if self.tools.is_done(response):
            self.trajectory.add(response)
            return response.content

        return self._execute_action(response)

    def _execute_action(self, response: Response) -> None:
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
        ("agent.py", "updated", "Added `NativeTools`!"),
        ("llm.py", None, ""),
        ("memory.py", None, ""),
        ("toolbox.py", "new", "This file tracks all tools that were created for easy reference."),
        ("tools.py", "new", "Created a tool registry, parsing, and execution class."),
    ]
)

llm_diff = DiffViewer(ch2.LLM.generate, LLM.generate, "ch2.LLM", "ch5.LLM")
tinyagents_diff = DiffViewer(ch5.TinyAgent, TinyAgent, "ch5.TinyAgent", "ch5_native.TinyAgent")

what_we_built = ChapterOverview(
    [
        ("agent.py", "updated", "Updated `TinyAgent` to handle native tool calling."),
        ("llm.py", "updated", "Extract tool calls from LLM response metadata instead of text parsing."),
        ("memory.py", "updated", "Track tool calling and observations in memory."),
        ("toolbox.py", None, ""),
        ("tools.py", "updated", "Create `NativeTools` for native tool calling."),
        ("trajectory.py", None, ""),
    ]
)


# add_nativetool_annotated = CodeAnnotator(
#     NativeTools.has_tool_call,
#     annotations={
#         3: """We check whether there is a tool call by seeing if `"tool":` appears in the text. If it does, we think there is a tool call. """
#     },
# )

# parse_tool_annotated = CodeAnnotator(
#     NativeTools.parse_tool_call,
#     annotations={3: "We expect a simple JSON string and only need to extract within {} brackets."},
# )

# run_tool_annotated = CodeAnnotator(
#     NativeTools.run_tool,
#     annotations={
#         7: "The tool name and possible arguments are extracted from the parsed tool call.",
#         (11, 12): "Tools are looked up in the registry and executed with the provided arguments.",
#     },
# )
