import litellm
import ollama


class LLM:
    def __init__(self, model: str, think: bool = False, **kwargs):
        """Initialize the LLM with the given model."""
        self.model = model
        self.think = think
        self.kwargs = kwargs

    def generate(self, messages: list[dict]) -> str:
        """Generate a response from the LLM given a list of messages."""

        # LiteLLM
        if "/" in self.model:
            response = litellm.completion(model=self.model, messages=messages, **self.kwargs)
            return response.choices[0].message.content

        # Native Ollama
        else:
            response = ollama.chat(model=self.model, messages=messages, think=self.think, **self.kwargs)
            return response.message.content
