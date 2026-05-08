from openai import OpenAI

from dataclasses import dataclass

from illustrated_agents.utils import CodeAnnotator, DiffViewer, ChapterOverview
from illustrated_agents.chapters import ch1


@dataclass
class Response:
    """Structured response from LLM calls."""

    content: str = ""
    reasoning: str | None = None
    tool_call: dict | None = None
    metadata: dict | None = None


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
            extra_body = {
                "chat_template_kwargs": {"enable_thinking": False},
                "reasoning_effort": "none",
            }

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


@dataclass
class Step:
    """A single step in an agent's trajectory."""

    thought: str = ""
    action: dict | None = None
    observation: str | None = None
    answer: str | None = None
    metadata: dict | None = None


class Trajectory:
    """Records agent execution as a sequence of runs."""

    def __init__(self) -> None:
        self.runs: list[dict] = []

    def initialize(self, query: str) -> None:
        """Register a new run with the given query."""
        self.runs.append({"query": query, "steps": []})

    def add(self, response: Response, observation: str | None = None) -> None:
        """Record a step from a Response, optionally with an observation."""
        # Add THOUGHT
        step = Step(
            thought=response.reasoning or "",
            metadata=response.metadata,
        )

        # Add ACTION/OBSERVATION or ANSWER
        if observation is not None:
            step.action = response.tool_call
            step.observation = observation
        else:
            step.answer = response.content

        self.runs[-1]["steps"].append(step)


class TinyAgent:
    """A minimal, modular, and educational agent framework."""

    def __init__(self, llm: LLM):
        self.llm = llm
        self.memory = None  # Chapter 4: Add Memory
        self.tools = None  # Chapter 5: Add Tools
        self.planner = None  # Chapter 6: Add Planning
        self.skills = None  # Chapter 6: Add Skills

        self.trajectory = Trajectory()

    def run(self, task: str) -> str:
        """Run the agent on a task."""
        self.trajectory.initialize(task)
        return self._step(task)

    def _step(self, task: str) -> str:
        """Perform a single step."""
        messages = [{"role": "user", "content": task}]
        response = self.llm.generate(messages)
        self.trajectory.add(response)
        return response.content

    def _execute_action(self, action: str) -> str | None:
        """Execute a tool action."""
        # Placeholder - will be implemented in later chapters
        return f"Executed action: {action}"


what_we_built = ChapterOverview(
    [
        ("agent.py", "updated", "Integrated the `LLM` into your `TinyAgent`"),
        ("llm.py", "new", "An LLM wrapper for local or cloud models."),
        ("trajectory.py", "new", "A structured way to record agent execution."),
    ]
)


trajectory_add_annotated = CodeAnnotator(
    Trajectory.add,
    annotations={
        (
            4,
            7,
        ): "Add the potential reasoning (THOUGHT) and metadata from the LLM response to the step.",
        (
            11,
            12,
        ): "Add the tool call (ACTION) and observation (OBSERVATION)",
        14: "If there's no observation, this is a final answer (ANSWER)",
        17: "Finally, we add the step to the list.",
    },
)


llm_annotated = CodeAnnotator(
    LLM.generate,
    annotations={
        (
            13,
            19,
        ): "We call the 'completion' function with any additional keyword arguments which gives back the `response` object from the OpenAI API.",
        (
            22,
            29,
        ): "We then extract the content, reasoning, tool calls, and metadata from the response",
        (32, 37): "Finally, we format this into our `Response` dataclass and return it.",
    },
)
tinyagents_diff = DiffViewer(ch1.TinyAgent, TinyAgent, "ch1.TinyAgent", "ch2.TinyAgent")
