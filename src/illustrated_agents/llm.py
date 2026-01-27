from litellm import completion


class LLM:
    def __init__(self, model: str, **kwargs):
        """Initialize the LLM with the given model."""
        self.model = model
        self.kwargs = kwargs

    def generate(self, messages: list[dict]) -> str:
        """Generate a response from the LLM given a list of messages."""
        # Call the chat completion function
        response = completion(model=self.model, messages=messages, **self.kwargs)

        # Extract and return the output text
        output = response.choices[0].message.content
        return output
