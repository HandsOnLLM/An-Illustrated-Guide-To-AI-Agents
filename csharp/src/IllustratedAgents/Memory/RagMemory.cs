using System.Text.Json.Nodes;

namespace IllustratedAgents;

/// <summary>
/// Long-term memory with retrieval-augmented generation: every user message is stored together with the
/// documents most similar to it. Chapter 4.
/// </summary>
/// <remarks>
/// Embedding the documents needs a model call, and a constructor can't be awaited, so you build one
/// with <see cref="CreateAsync"/>.
/// </remarks>
public class RagMemory : Memory
{
    private readonly IEmbeddingModel _embeddingModel;

    private RagMemory(IEmbeddingModel embeddingModel, IReadOnlyList<string> documents, IReadOnlyList<float[]> embeddings)
    {
        _embeddingModel = embeddingModel;
        Documents = documents;
        Embeddings = embeddings;
    }

    public IReadOnlyList<string> Documents { get; }
    public IReadOnlyList<float[]> Embeddings { get; }

    /// <summary>Embed every document once, up front, and return the memory.</summary>
    public static async Task<RagMemory> CreateAsync(
        IEmbeddingModel embeddingModel,
        IReadOnlyList<string> documents,
        CancellationToken cancellationToken = default)
    {
        var embeddings = new List<float[]>();
        foreach (var document in documents)
        {
            embeddings.Add(await embeddingModel.EmbedAsync(document, cancellationToken));
        }
        return new RagMemory(embeddingModel, documents, embeddings);
    }

    public override async Task AddAsync(
        string role,
        string? content,
        JsonObject? toolCall = null,
        string? imageData = null,
        CancellationToken cancellationToken = default)
    {
        // Augment user questions with retrieved context before storing them
        if (role == "user" && content is not null)
        {
            var context = string.Join("\n", await SearchAsync(content, cancellationToken: cancellationToken));
            content = $"""
                Context:
                {context}

                Question: {content}
                """;
        }
        await base.AddAsync(role, content, toolCall, imageData, cancellationToken);
    }

    /// <summary>The <paramref name="k"/> documents most similar to <paramref name="query"/>, best first.</summary>
    public async Task<IReadOnlyList<string>> SearchAsync(string query, int k = 3, CancellationToken cancellationToken = default)
    {
        var queryEmbedding = await _embeddingModel.EmbedAsync(query, cancellationToken);
        return Enumerable.Range(0, Documents.Count)
            .OrderByDescending(i => Cosine(queryEmbedding, Embeddings[i]))
            .Take(k)
            .Select(i => Documents[i])
            .ToList();
    }

    /// <summary>Cosine similarity: 1 means the same direction, 0 unrelated, -1 opposite.</summary>
    public static double Cosine(float[] a, float[] b)
    {
        double dot = 0, normA = 0, normB = 0;
        for (var i = 0; i < Math.Min(a.Length, b.Length); i++)
        {
            dot += a[i] * b[i];
            normA += a[i] * a[i];
            normB += b[i] * b[i];
        }
        return dot / (Math.Sqrt(normA) * Math.Sqrt(normB));
    }
}
