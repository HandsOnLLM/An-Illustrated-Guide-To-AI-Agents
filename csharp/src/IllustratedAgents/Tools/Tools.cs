using System.Text.Json;
using System.Text.Json.Nodes;

namespace IllustratedAgents;

/// <summary>A registered tool: the C# function that does the work, and how the model should use it.</summary>
public sealed record ToolEntry(Delegate Function, string Description);

/// <summary>
/// The tool registry, using text-based tool calling: the model writes a JSON blob such as
/// <c>{"tool": "multiply", "kwargs": {"a": "5.1", "b": "7.3"}}</c> in its reply. Chapter 5.
/// </summary>
public class Tools
{
    private static readonly JsonDocumentOptions LenientJson = new() { AllowTrailingCommas = true };

    private readonly Func<string, bool> _approve;

    /// <param name="requiresApproval">Tools that must be approved by a person before they run.</param>
    /// <param name="approve">
    /// Asks a person whether a tool may run. Defaults to a yes/no question on the console; tests pass their own.
    /// </param>
    public Tools(IEnumerable<string>? requiresApproval = null, Func<string, bool>? approve = null)
    {
        RequiresApproval = new HashSet<string>(requiresApproval ?? []);
        _approve = approve ?? AskOnConsole;
    }

    /// <summary>Every registered tool by name, in the order they were added.</summary>
    public OrderedDictionary<string, ToolEntry> Registry { get; } = new();

    public ISet<string> RequiresApproval { get; }

    /// <summary>Register a tool the agent can use.</summary>
    public void AddTool(string name, Delegate function, string description = "")
    {
        Registry[name] = new ToolEntry(function, description);
    }

    /// <summary>One line per tool: <c>`name`: description</c>.</summary>
    public string Descriptions
    {
        get
        {
            return string.Join("\n", Registry.Select(tool => $"`{tool.Key}`: {tool.Value.Description}"));
        }
    }

    /// <summary>The part of the system prompt that tells the model which tools exist and how to call one.</summary>
    public virtual string Prompt
    {
        get
        {
            return $$$"""

                # Tools

                If needed, you can only use the following tools to assist you in completing tasks:

                {{{Descriptions}}}

                To use a tool, respond with JSON: {"tool": "name", "kwargs": {"param": "value"}}

                """;
        }
    }

    /// <summary>Native tool definitions to send with the request. Text-based tools send none.</summary>
    public virtual JsonArray? Schemas => null;

    /// <summary>
    /// Find a JSON tool call in the model's text and attach it to the response as
    /// <c>{"tool": ..., "kwargs": ...}</c>. Text with no tool call comes back unchanged.
    /// </summary>
    public virtual Response Parse(Response response)
    {
        var text = response.Content;
        if (!text.Contains("\"tool\":") && !text.Contains("\"tool:\""))
        {
            return response;
        }

        var start = text.IndexOf('{');
        var end = text.LastIndexOf('}');
        if (start < 0 || end <= start)
        {
            return response;
        }

        try
        {
            var toolCall = JsonNode.Parse(text[start..(end + 1)], documentOptions: LenientJson) as JsonObject;
            if (toolCall is null)
            {
                return response;
            }

            // Return a new response carrying the parsed tool call
            return new Response
            {
                Content = response.Content,
                Reasoning = response.Reasoning,
                ToolCall = toolCall,
                Metadata = response.Metadata,
            };
        }
        catch (JsonException)
        {
            // Not valid JSON after all: treat the reply as plain text
            return response;
        }
    }

    /// <summary>
    /// Run the tool named in <c>response.ToolCall</c>. Asks for approval first when the tool requires it.
    /// Unknown tools, denied tools and tools that throw all come back as a message for the model, not an exception.
    /// </summary>
    public virtual async Task<object?> ExecuteAsync(Response response, CancellationToken cancellationToken = default)
    {
        var toolCall = response.ToolCall ?? throw new InvalidOperationException("The response has no tool call.");
        var name = toolCall["tool"]?.GetValue<string>() ?? "";
        var kwargs = toolCall["kwargs"];

        if (!Registry.TryGetValue(name, out var entry))
        {
            return $"Tool '{name}' not found.";
        }

        // Human in the loop: ask before running dangerous tools
        if (RequiresApproval.Contains(name) && !_approve(name))
        {
            return $"Tool '{name}' was denied by the user.";
        }

        try
        {
            return await ToolInvoker.InvokeAsync(entry.Function, kwargs, cancellationToken);
        }
        catch (Exception ex) when (ex is not OperationCanceledException)
        {
            // Hand the error back as an observation so the model can try again
            return $"Error running tool '{name}': {ex.Message}";
        }
    }

    /// <summary>How a tool result goes back into memory: here, as a user message starting with OBSERVATION.</summary>
    public virtual (string Role, string Content) Observation(object? result)
    {
        return ("user", $"OBSERVATION: {ToolInvoker.Format(result)}");
    }

    /// <summary>
    /// The stopping rule. Done when there is no tool call, or when the tool is <c>final_answer</c>, in which
    /// case its kwargs become the response's content.
    /// </summary>
    public virtual bool IsDone(Response response)
    {
        if (response.ToolCall is null)
        {
            return true;
        }

        if (response.ToolCall["tool"]?.GetValue<string>() == "final_answer")
        {
            var kwargs = response.ToolCall["kwargs"];

            // Usually a plain string; some models wrap it as {"answer": "..."} instead
            if (kwargs is JsonObject { Count: 1 } wrapper && wrapper.First().Value is JsonValue inner)
            {
                kwargs = inner;
            }

            response.Content = kwargs is JsonValue value && value.TryGetValue<string>(out var text)
                ? text
                : kwargs?.ToJsonString() ?? "";
            return true;
        }

        return false;
    }

    private static bool AskOnConsole(string toolName)
    {
        Console.Write($"Allow {toolName}? [y/N] ");
        var answer = Console.ReadLine()?.Trim().ToLowerInvariant();
        return answer is "y" or "yes";
    }
}
