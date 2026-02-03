from illustrated_agents import LLM, Memory
from illustrated_agents.utils import CodeAnnotator, DiffViewer
from illustrated_agents.chapters import ch2


class TinyAgent:
    """A minimal, modular, and educational agent framework."""

    def __init__(self, llm: LLM, memory: Memory):
        self.llm = llm
        self.memory = memory
        self.tools = None  # Chapter 5: Add Tools
        self.planner = None  # Chapter 6: Add Planning
        self.reflector = None  # Chapter 6: Add Reflection
        self.skills = None  # Chapter 6: Add Skills

    def run(self, task: str) -> str:
        """Run the agent on a task."""
        return self._step(task)

    def _step(self, task: str) -> str:
        """Perform a single step."""
        # 1. Every step, we add the user task to memory
        self.memory.add("user", task)

        # 2. Then, we generate a response based on the conversation history
        response = self.llm.generate(self.memory.get_messages())

        # 3. Finally, we add the assistant's response to memory
        self.memory.add("assistant", response)
        return response


memory_annotated = CodeAnnotator(
    Memory,
    annotations={
        5: "We keep track of a list of messages where each message is a dict with 'role' and 'content'.",
        (7, 9): """Whenever we add a new message, we append it to the list of messages and define the 
        role (e.g., 'user' or 'assistant') and the content of the message.""",
        (11, 13): "To retrieve the conversation history, we simply return the list of messages stored in memory.",
    },
)

tinyagents_diff = DiffViewer(ch2.TinyAgent, TinyAgent, "ch2.TinyAgent", "ch4.TinyAgent")
