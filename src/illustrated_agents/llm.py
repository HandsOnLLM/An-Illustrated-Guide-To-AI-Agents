import litellm
import ollama

from openai import OpenAI
from enum import StrEnum
from dataclasses import dataclass


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
