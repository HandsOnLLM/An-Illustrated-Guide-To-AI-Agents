class Memory:
    """Simple memory module to store conversation history."""

    def __init__(self):
        self.messages = []

    def add(self, role: str, content: str, tool_calls: list = None, image_url: str = None):
        """Add a message to memory."""
        message = {"role": role, "content": content}

        # Tool call
        if tool_calls:
            message["tool_calls"] = tool_calls

        # Add Image
        if image_url:
            message["content"] = [
                {"type": "text", "text": content},
                {"type": "image_url", "image_url": {"url": image_url}},
            ]

        # Append message to memory
        self.messages.append(message)

    def get_messages(self) -> list[dict]:
        """Get all messages."""
        return self.messages
