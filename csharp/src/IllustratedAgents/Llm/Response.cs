using System.Text.Json.Nodes;

namespace IllustratedAgents;

/// <summary>
/// What one call to the model produced. Planners and tool registries rewrite these fields as the
/// response moves through the agent loop, so it is a mutable class rather than a record.
/// </summary>
public sealed class Response
{
    /// <summary>The visible text the model wrote. Never null: an empty string when the model only called a tool.</summary>
    public string Content { get; set; } = "";

    /// <summary>The model's reasoning (THOUGHT), when the model or a planner provides it.</summary>
    public string? Reasoning { get; set; }

    /// <summary>
    /// A tool call. Straight from the API it looks like <c>{"id", "type", "function": {"name", "arguments"}}</c>;
    /// after a tool registry parses it, it looks like <c>{"tool": name, "kwargs": arguments}</c>.
    /// </summary>
    public JsonObject? ToolCall { get; set; }

    /// <summary>Which model answered and how many tokens it used.</summary>
    public ResponseMetadata? Metadata { get; set; }

    public override string ToString() =>
        $"Response {{ Content = {Content}, Reasoning = {Reasoning ?? "null"}, ToolCall = {ToolCall?.ToJsonString() ?? "null"} }}";
}

/// <summary>Bookkeeping about a model call.</summary>
public sealed record ResponseMetadata(string Model, int PromptTokens, int CompletionTokens);
