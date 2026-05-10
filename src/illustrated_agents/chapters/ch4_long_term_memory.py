from openai import OpenAI

from illustrated_agents.utils import ChapterOverview
from illustrated_agents.chapters.ch4 import Memory


class EmbeddingModel:
    """A model to generate embeddings."""

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


class LongTermMemory(Memory):
    """Memory enhanced with RAG: augments user queries with retrieved documents."""

    def __init__(self, embedding_model: EmbeddingModel, documents: list[str]):
        super().__init__()
        self.embedding_model = embedding_model
        self.documents = documents
        self.embeddings = [embedding_model.embed(doc) for doc in documents]

    def add(self, role: str, content: str):
        # Augment user queries with retrieved context before storing
        if role == "user":
            context = "\n".join(self.search(content))
            content = f"""Context:
{context}

Question: {content}"""
        super().add(role, content)

    def search(self, query: str) -> list[str]:
        """Return the top-k documents most similar to the query."""
        query_embed = self.embedding_model.embed(query)
        scores = [self._cosine(query_embed, embed) for embed in self.embeddings]
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        return [self.documents[index] for index in ranked[:3]]

    def _cosine(self, a: list[float], b: list[float]) -> float:
        """Calculate cosine similarity between two embeddings.."""
        dot = sum(x * y for x, y in zip(a, b))
        norm = (sum(x * x for x in a) ** 0.5) * (sum(x * x for x in b) ** 0.5)
        return dot / norm


what_we_built = ChapterOverview(
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
