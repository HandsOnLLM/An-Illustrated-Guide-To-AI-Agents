using System.Text.Json.Nodes;

namespace IllustratedAgents;

/// <summary>
/// Anything that can turn a conversation into a <see cref="Response"/>. The real implementation is
/// <see cref="Llm"/>; the tests use a scripted fake, which is why the agent depends on this interface.
/// </summary>
public interface ILlm
{
    /// <summary>Generate a response to <paramref name="messages"/>, optionally offering native <paramref name="tools"/>.</summary>
    Task<Response> GenerateAsync(
        IReadOnlyList<ChatMessage> messages,
        JsonArray? tools = null,
        CancellationToken cancellationToken = default);
}

/// <summary>Anything that can turn text into a vector of numbers (chapter 4's long-term memory).</summary>
public interface IEmbeddingModel
{
    Task<float[]> EmbedAsync(string text, CancellationToken cancellationToken = default);
}
