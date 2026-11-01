using System.Text.Json.Nodes;

namespace IllustratedAgents;

/// <summary>
/// One message in a conversation: who said it (<see cref="Role"/>) and what they said.
/// Roles are "system", "user", "assistant" and, for native tool calling, "tool".
/// </summary>
/// <remarks>
/// The Python version stores messages as dicts. A record keeps the same shape but lets the
/// compiler catch typos in field names.
/// </remarks>
public sealed record ChatMessage(string Role, string? Content)
{
    /// <summary>
    /// Multimodal content (chapter 9). When set, it replaces <see cref="Content"/> in the request:
    /// an image part followed by a text part.
    /// </summary>
    public IReadOnlyList<ContentPart>? Parts { get; init; }

    /// <summary>The tool call the model made in this message, exactly as the API returned it.</summary>
    public JsonObject? ToolCall { get; init; }
}

/// <summary>One piece of a multimodal message: either text or an image URL (which may be a data URL).</summary>
public sealed record ContentPart(string Type, string? Text = null, string? ImageUrl = null)
{
    public static ContentPart FromText(string text) => new("text", Text: text);

    public static ContentPart FromImageUrl(string url) => new("image_url", ImageUrl: url);
}
