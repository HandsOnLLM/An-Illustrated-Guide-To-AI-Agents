from openai import OpenAI
from dataclasses import dataclass


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


class EmbeddingModel:
    """A model to generate embeddings."""

    def __init__(self, model: str, client: OpenAI):
        self.model = model
        self.client = client

    def embed(self, text: str) -> list[float]:
        """Convert text into a numerical vector."""
        return self.client.embeddings.create(model=self.model, input=text).data[0].embedding
