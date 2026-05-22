import json
import urllib.request
from dataclasses import dataclass


@dataclass
class Response:
    """Structured response from LLM calls."""

    content: str = ""
    reasoning: str | None = None
    tool_call: dict | None = None
    metadata: dict | None = None


class LLM:
    def __init__(
        self,
        model: str,
        base_url: str = "http://localhost:11434/v1",
        api_key: str = "no_key",
        think: bool = False,
        **kwargs,
    ):
        """Initialize the LLM with the given model."""
        self.model = model
        self.base_url = base_url
        self.api_key = api_key
        self.think = think
        self.kwargs = kwargs

    def generate(
        self, messages: list[dict], tools: list | None = None
    ) -> Response:
        """Generate a response from the LLM given a list of messages."""
        # Build the request body
        body = {
            "model": self.model,
            "messages": messages,
            **self.kwargs,
        }
        if tools:
            body["tools"] = tools

        # Enable/Disable thinking
        if not self.think:
            body["reasoning_effort"] = "none"

        # POST to the OpenAI-compatible /chat/completions endpoint
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(body).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )
        with urllib.request.urlopen(request) as response:
            data = json.loads(response.read())

        # Extract message, tool_call, and metadata
        message = data["choices"][0]["message"]
        tool_calls = message.get("tool_calls")
        tool_call = tool_calls[0] if tool_calls else None
        metadata = {
            "model": data["model"],
            "prompt_tokens": data["usage"]["prompt_tokens"],
            "completion_tokens": data["usage"]["completion_tokens"],
        }

        # Format as Response dataclass
        return Response(
            content=message.get("content"),
            reasoning=message.get("reasoning"),
            tool_call=tool_call,
            metadata=metadata,
        )


class OpenAIClientLLM:
    def __init__(self, model: str, client, think: bool = False, **kwargs):
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
            reasoning=getattr(message, "reasoning_content", None)
            or getattr(message, "reasoning", None),
            tool_call=tool_call,
            metadata=metadata,
        )


class EmbeddingModel:
    """Generate embeddings."""

    def __init__(
        self,
        model: str,
        base_url: str = "http://localhost:11434/v1",
    ):
        """Initialize the embedding model with the given model."""
        self.model = model
        self.base_url = base_url

    def embed(self, text: str) -> list[float]:
        """Convert text into a numerical vector."""
        # POST to the OpenAI-compatible /embeddings endpoint
        request = urllib.request.Request(
            f"{self.base_url}/embeddings",
            data=json.dumps({"model": self.model, "input": text}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request) as resp:
            response = json.loads(resp.read())

        # Extract and return the embedding
        return response["data"][0]["embedding"]
