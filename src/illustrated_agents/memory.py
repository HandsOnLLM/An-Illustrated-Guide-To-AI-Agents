class Memory:
    """Simple memory module to store conversation history."""

    def __init__(self):
        self.messages = []

    def add(self, role: str, content: str):
        """Add a message to memory."""
        self.messages.append({"role": role, "content": content})

    def get_messages(self) -> list[dict]:
        """Get all messages."""
        return self.messages
