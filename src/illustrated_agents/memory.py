class Memory:
    """Simple memory module to store conversation history."""

    def __init__(self):
        self.messages = []

    def add(self, role: str, content: str, image_url: str = None):
        """Add a message to memory."""
        if image_url:
            content = [{"type": "text", "text": content}, {"type": "image_url", "image_url": {"url": image_url}}]
        self.messages.append({"role": role, "content": content})

    def get_messages(self) -> list[dict]:
        """Get all messages."""
        return self.messages
