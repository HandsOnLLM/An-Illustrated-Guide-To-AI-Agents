using System.Text.Json.Nodes;

namespace IllustratedAgents;

/// <summary>
/// Conversation history: every message the agent has seen and said, in order. Chapter 4.
/// </summary>
/// <remarks>
/// <see cref="AddAsync"/> is async because some memories (summarization, RAG) call a model while
/// adding. The plain memory finishes immediately.
/// </remarks>
public class Memory
{
    public List<ChatMessage> Messages { get; protected set; } = [];

    /// <summary>
    /// Add a message. <paramref name="toolCall"/> is the raw tool call the model made, if any.
    /// <paramref name="imageData"/> is a URL or base64 image; plain memory ignores it (see chapter 9).
    /// </summary>
    public virtual Task AddAsync(
        string role,
        string? content,
        JsonObject? toolCall = null,
        string? imageData = null,
        CancellationToken cancellationToken = default)
    {
        Messages.Add(new ChatMessage(role, content) { ToolCall = toolCall });
        return Task.CompletedTask;
    }

    /// <summary>Every message, in the order they were added.</summary>
    public virtual IReadOnlyList<ChatMessage> GetMessages()
    {
        return Messages;
    }
}
