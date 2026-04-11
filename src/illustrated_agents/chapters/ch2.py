import litellm
import ollama
from openai import OpenAI

from enum import StrEnum
from dataclasses import dataclass

from illustrated_agents.utils import CodeAnnotator, DiffViewer, ChapterOverview
from illustrated_agents.chapters import ch1


class Backend(StrEnum):
    LITELLM = "litellm"
    OPENAI = "openai"
    OLLAMA = "ollama"


@dataclass
class Response:
    """Structured response from LLM calls."""

    content: str = ""
    reasoning: str = None
    tool_call: dict = None


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

    def generate(self, messages: list[dict]) -> Response:
        """Generate a response from the LLM given a list of messages."""

        # LiteLLM
        if self.backend == Backend.LITELLM:
            return self.litellm(messages)

        # OpenAI API
        elif self.backend == Backend.OPENAI:
            return self.openai(messages)

        # Ollama
        elif self.backend == Backend.OLLAMA:
            return self.ollama(messages)

        else:
            raise ValueError(f"Unsupported backend: {self.backend}")

    def ollama(self, messages: list[dict]) -> Response:
        """Generate a response from Ollama."""
        response = ollama.chat(
            model=self.model,
            messages=messages,
            think=self.think,
            **self.kwargs,
        )

        # Format as Response dataclass
        message = response.message
        response = Response(
            content=message.content,
            reasoning=getattr(message, "thinking", None),
        )
        return response

    def openai(self, messages: list[dict]) -> Response:
        """Generate a response from the OpenAI API."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}, "reasoning_effort": "none"}
            if not self.think
            else None,
            **self.kwargs,
        )

        # Format as Response dataclass
        message = response.choices[0].message
        response = Response(
            content=message.content,
            reasoning=getattr(message, "reasoning_content", None) or getattr(message, "reasoning", None),
        )
        return response

    def litellm(self, messages: list[dict]) -> Response:
        """Generate a response from LiteLLM."""
        response = litellm.completion(
            model=self.model,
            messages=messages,
            api_base=self.api_base,
            api_key=self.api_key,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}, "reasoning_effort": "none"}
            if not self.think
            else None,
            **self.kwargs,
        )

        # Format as Response dataclass
        message = response.choices[0].message
        response = Response(
            content=message.content,
            reasoning=getattr(message, "reasoning_content", None) or getattr(message, "reasoning", None),
        )
        return response


class TinyAgent:
    """A minimal, modular, and educational agent framework."""

    def __init__(self, llm: LLM):
        self.llm = llm
        self.memory = None  # Chapter 4: Add Memory
        self.tools = None  # Chapter 5: Add Tools
        self.planner = None  # Chapter 6: Add Planning
        self.skills = None  # Chapter 6: Add Skills

    def run(self, task: str) -> str:
        """Run the agent on a task."""
        return self._step(task)

    def _step(self, task: str) -> str:
        """Perform a single step."""
        messages = [{"role": "user", "content": task}]
        response = self.llm.generate(messages)
        return response.content

    def _execute_action(self, action: str) -> str | None:
        """Execute a tool action."""
        # Placeholder - will be implemented in later chapters
        return f"Executed action: {action}"


what_we_built = ChapterOverview(
    [
        ("agent.py", "updated", "Integrated the `LLM` into your `TinyAgent`"),
        ("llm.py", "new", "An LLM wrapper for local or cloud models."),
    ]
)


llm_annotated = CodeAnnotator(
    LLM.openai,
    annotations={
        (
            3,
            9,
        ): "We call the 'completion' function with any additional keyword arguments which gives back the `response` object from the LLM API.",
        (
            13,
            18,
        ): "Although some LLMs return explicit tool calls or reasoning traces, we simply extract the answer only. This allows us to create Agents from any LLM, even those that don't support tool calls natively.",
    },
)

tinyagents_diff = DiffViewer(ch1.TinyAgent, TinyAgent, "ch1.TinyAgent", "ch2.TinyAgent")
