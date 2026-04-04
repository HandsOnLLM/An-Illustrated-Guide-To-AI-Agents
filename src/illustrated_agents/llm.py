from dataclasses import dataclass

import litellm
import ollama

from illustrated_agents.utils import function_to_dict


@dataclass
class Response:
    """Structured response from LLM calls."""

    content: str = ""
    reasoning: str = ""
    tool_calls: list = None


class LLM:
    def __init__(self, model: str, think: bool = False, **kwargs):
        """Initialize the LLM with the given model."""
        self.model = model
        self.think = think
        self.kwargs = kwargs

    def generate(self, messages: list[dict], tools: list = None) -> Response:
        """Generate a response from the LLM given a list of messages."""

        # LiteLLM
        if "/" in self.model:
            kwargs = {**self.kwargs}
            if tools:
                kwargs["tools"] = [{"type": "function", "function": function_to_dict(function)} for function in tools]
            message = litellm.completion(model=self.model, messages=messages, **kwargs).choices[0].message
            tool_calls = [tool_call.model_dump() for tool_call in message.tool_calls] if message.tool_calls else None

        # Native Ollama
        else:
            message = ollama.chat(model=self.model, messages=messages, tools=tools, think=self.think).message
            tool_calls = (
                [{"function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in message.tool_calls]
                if message.tool_calls
                else None
            )

        return Response(
            content=message.content or "",
            reasoning=getattr(message, "reasoning_content", None) or getattr(message, "thinking", None) or "",
            tool_calls=tool_calls,
        )
