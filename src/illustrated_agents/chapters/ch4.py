from illustrated_agents.utils import CodeAnnotator, DiffViewer, ChapterOverview
from illustrated_agents.chapters.ch2 import LLM, Trajectory
from illustrated_agents.chapters import ch2


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


class TinyAgent:
    """A minimal, modular, and educational agent framework."""

    def __init__(self, llm: LLM, memory: Memory):
        self.llm = llm
        self.memory = memory
        self.tools = None  # Chapter 5: Add Tools
        self.planner = None  # Chapter 6: Add Planning
        self.skills = None  # Chapter 6: Add Skills

        self.trajectory = Trajectory()

    def run(self, task: str) -> str:
        """Run the agent on a task."""
        self.memory.add("user", task)
        self.trajectory.initialize(task)

        return self._step()

    def _step(self) -> str:
        """Perform a single step."""
        # Generate response and add to memory
        response = self.llm.generate(self.memory.get_messages())
        self.memory.add("assistant", response.content)
        self.trajectory.add(response)
        return response.content

    def _execute_action(self, action: str) -> str | None:
        """Execute a tool action."""
        # Placeholder - will be implemented in later chapters
        return f"Executed action: {action}"


what_we_built = ChapterOverview(
    [
        ("agent.py", "updated", "Integrated `Memory` into your `TinyAgent`."),
        ("llm.py", None, ""),
        ("memory.py", "new", "Track conversation history."),
        ("trajectory.py", None, ""),
    ]
)


tinyagent_annotated = CodeAnnotator(
    TinyAgent,
    annotations={
        15: "1. The user's query is added to the `Memory` module",
        23: "2. Based on the current memory, the LLM generates a response.",
        24: "3. The response of the LLM is added to the `Memory` module.",
    },
)


memory_annotated = CodeAnnotator(
    Memory,
    annotations={
        5: "We keep track of a list of messages where each message is a dict with 'role' and 'content'.",
        (7, 9): """Whenever we add a new message, we append it to the list of messages and define the 
        role (e.g., 'user' or 'assistant') and the content of the message.""",
        (
            11,
            13,
        ): "To retrieve the conversation history, we simply return the list of messages stored in memory.",
    },
)

tinyagents_diff = DiffViewer(ch2.TinyAgent, TinyAgent, "ch2.TinyAgent", "ch4.TinyAgent")
