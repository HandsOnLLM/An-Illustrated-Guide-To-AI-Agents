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

        # If this is a tool message, link it to the previous message's tool call ID
        if role == "tool" and self.messages:
            prev = self.messages[-1]
            if "tool_calls" in prev:
                message["tool_call_id"] = prev["tool_calls"][0].get("id", "")

        # Add Image
        if image_url:
            message["content"] = [{"type": "text", "text": content}, {"type": "image_url", "image_url": {"url": image_url}}]

        # Append message to memory
        self.messages.append(message)

    def get_messages(self) -> list[dict]:
        """Get all messages."""
        return self.messages
