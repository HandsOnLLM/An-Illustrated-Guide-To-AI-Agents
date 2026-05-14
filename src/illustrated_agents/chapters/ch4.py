from openai import OpenAI

from illustrated_agents.utils import CodeAnnotator, DiffViewer, ChapterOverview
from illustrated_agents.chapters.ch2 import LLM, Trajectory
from illustrated_agents.chapters import ch2


class EmbeddingModel:
    """Wrapper around an embedding model, mirroring the `LLM` class."""

    def __init__(self, model: str, client: OpenAI):
        self.model = model
        self.client = client

    def embed(self, text: str) -> list[float]:
        """Convert text into a numerical vector."""
        return (
            self.client.embeddings.create(model=self.model, input=text)
            .data[0]
            .embedding
        )


class Memory:
    """Simple memory module to store conversation history."""

    def __init__(self):
        self.messages = []

    def add(self, role: str, content: str, tool_call: dict | None = None) -> None:
        """Add a message to memory."""
        message = {"role": role, "content": content}

        # Tool call
        if tool_call:
            message["tool_calls"] = [tool_call]

        # Append message to memory
        self.messages.append(message)

    def get_messages(self) -> list[dict]:
        """Get all messages."""
        return self.messages


class TrimmingMemory(Memory):
    """Memory that keeps only the last two user/assistant turns."""

    def add(self, role: str, content: str) -> None:
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

    def add(self, role: str, content: str) -> None:
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


class LongTermMemory(Memory):
    """Memory enhanced with RAG: augments user queries with retrieved documents."""

    def __init__(self, embedding_model: EmbeddingModel, documents: list[str]):
        super().__init__()
        self.embedding_model = embedding_model
        self.documents = documents
        self.embeddings = [embedding_model.embed(doc) for doc in documents]

    def add(self, role: str, content: str) -> None:
        # Augment user queries with retrieved context before storing
        if role == "user":
            context = "\n".join(self.search(content))
            content = f"""Context:
{context}

Question: {content}"""
        super().add(role, content)

    def search(self, query: str, k: int = 3) -> list[str]:
        """Return the top-k documents most similar to the query."""
        query_embedding = self.embedding_model.embed(query)
        scores = [self._cosine(query_embedding, emb) for emb in self.embeddings]
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        return [self.documents[i] for i in ranked[:k]]

    def _cosine(self, a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm = (sum(x * x for x in a) ** 0.5) * (sum(x * x for x in b) ** 0.5)
        return dot / norm


class TinyAgent:
    """A minimal, modular, and educational agent framework."""

    def __init__(self, llm: LLM, memory: Memory):
        self.llm = llm
        self.memory = memory
        self.tools = None  # Chapter 5: Add Tools
        self.planner = None  # Chapter 6: Add Planning

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

what_we_built_lt = ChapterOverview(
    [
        ("agent.py", None, ""),
        (
            "llm.py",
            "updated",
            "Add `EmbeddingModel` to support long-term memory.",
        ),
        (
            "memory.py",
            "updated",
            "Add `LongTermMemory` to the TinyAgent in the form of RAG.",
        ),
        ("trajectory.py", None, ""),
    ]
)


what_we_built_st = ChapterOverview(
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
        9: """Whenever we add a new message, we append it to the list of messages and define the 
        role (e.g., 'user' or 'assistant') and the content of the message.""",
        (
            11,
            13,
        ): "Tool calls are tracked if they exist. This will be important in Chapter 5 when we add tools to our agent.",
        (
            18,
            20,
        ): "To retrieve the conversation history, we simply return the list of messages stored in memory.",
    },
)

tinyagents_diff = DiffViewer(
    ch2.TinyAgent, TinyAgent, "ch2.TinyAgent", "ch4.TinyAgent"
)
