from illustrated_agents.utils import ChapterOverview
from illustrated_agents.chapters.ch2 import LLM
from illustrated_agents.chapters.ch4 import Memory


class TrimmingMemory(Memory):
    """Memory that keeps only the last two user/assistant turns."""

    def add(self, role: str, content: str):
        # Add the new message first using the parent class (Memory)
        super().add(role, content)

        # Then, keep system message plus the most recent two turns (4 messages)
        system = [
            message for message in self.messages if message["role"] == "system"
        ]
        turns = [
            message for message in self.messages if message["role"] != "system"
        ]
        self.messages = system + turns[-4:]


class SummarizationMemory(Memory):
    """Memory that compresses past turns into a running summary via an LLM."""

    def __init__(self, llm: LLM):
        super().__init__()
        self.llm = llm

    def add(self, role: str, content: str):
        # Add the new message first using the parent class (Memory)
        super().add(role, content)

        # After each completed turn, update the running summary
        if role == "assistant":
            # Split the existing summary from the new conversation turns
            summary = ""
            conversation = ""
            for message in self.messages:
                if message["role"] == "system":
                    summary = message["content"]
                else:
                    conversation += f"{message['role']}: {message['content']}\n"

            # Ask the LLM to extend the summary with the new conversation
            prompt = f"""Update the summary with the new conversation.

Summary: {summary}

Conversation:
{conversation}
Output the updated summary only."""
            response = self.llm.generate([{"role": "user", "content": prompt}])
            self.messages = [{"role": "system", "content": response.content}]


what_we_built = ChapterOverview(
    [
        ("agent.py", None, ""),
        ("llm.py", None, ""),
        (
            "memory.py",
            "updated",
            "Add `TrimmingMemory` and `SummarizationMemory`.",
        ),
        ("trajectory.py", None, ""),
    ]
)
