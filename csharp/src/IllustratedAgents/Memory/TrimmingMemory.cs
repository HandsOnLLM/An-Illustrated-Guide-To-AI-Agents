using System.Text.Json.Nodes;

namespace IllustratedAgents;

/// <summary>Short-term memory that keeps the system message plus only the last two turns. Chapter 4.</summary>
public class TrimmingMemory : Memory
{
    /// <summary>How many non-system messages survive: two turns of user + assistant.</summary>
    public const int KeptMessages = 4;

    public override async Task AddAsync(
        string role,
        string? content,
        JsonObject? toolCall = null,
        string? imageData = null,
        CancellationToken cancellationToken = default)
    {
        // Add the new message first, using the base class
        await base.AddAsync(role, content, toolCall, imageData, cancellationToken);

        // Then keep the system messages plus the most recent turns
        var system = Messages.Where(m => m.Role == "system");
        var turns = Messages.Where(m => m.Role != "system").TakeLast(KeptMessages);
        Messages = [.. system, .. turns];
    }
}
