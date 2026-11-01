using System.Text.Json.Nodes;

namespace IllustratedAgents;

/// <summary>
/// The tool registry using native function calling: tools are sent as JSON schemas, and the model
/// returns a structured tool call instead of a JSON blob in its text. Chapter 5.
/// </summary>
public class NativeTools : Tools
{
    public NativeTools(IEnumerable<string>? requiresApproval = null, Func<string, bool>? approve = null)
        : base(requiresApproval, approve)
    {
    }

    /// <summary>One function definition per registered tool.</summary>
    public override JsonArray? Schemas
    {
        get
        {
            var schemas = new JsonArray();
            foreach (var (name, entry) in Registry)
            {
                schemas.Add(ToolSchema.FromDelegate(name, entry.Function, entry.Description));
            }
            return schemas;
        }
    }

    /// <summary>Native tool calling needs no instructions in the prompt.</summary>
    public override string Prompt
    {
        get
        {
            return "";
        }
    }

    /// <summary>
    /// Converts the API's <c>{"function": {"name", "arguments"}}</c> into <c>{"tool", "kwargs"}</c>.
    /// Arguments may arrive as a JSON string or as an object.
    /// </summary>
    public override Response Parse(Response response)
    {
        if (response.ToolCall is null)
        {
            return response;
        }

        // Extract the tool name and arguments
        var function = response.ToolCall["function"];
        var name = function?["name"]?.GetValue<string>() ?? "";
        var arguments = function?["arguments"];
        if (arguments is JsonValue value && value.TryGetValue<string>(out var json))
        {
            arguments = string.IsNullOrWhiteSpace(json) ? new JsonObject() : JsonNode.Parse(json);
        }

        return new Response
        {
            Content = response.Content,
            Reasoning = response.Reasoning,
            ToolCall = new JsonObject
            {
                ["tool"] = name,
                ["kwargs"] = arguments?.DeepClone() ?? new JsonObject(),
            },
            Metadata = response.Metadata,
        };
    }

    /// <summary>Native tool results go back with the "tool" role, with no OBSERVATION prefix.</summary>
    public override (string Role, string Content) Observation(object? result)
    {
        return ("tool", ToolInvoker.Format(result));
    }

    /// <summary>No tool call means the agent is done.</summary>
    public override bool IsDone(Response response)
    {
        return response.ToolCall is null;
    }
}
