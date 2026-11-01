using System.ComponentModel;
using System.Reflection;
using System.Text.Json.Nodes;

namespace IllustratedAgents;

/// <summary>
/// A minimal MCP server over stdio: enough to answer <c>initialize</c>, <c>ping</c>, <c>tools/list</c>
/// and <c>tools/call</c>. Provided for you, the way the Python book uses an existing MCP library for its
/// server. The exercise in chapter 5 is the client. Tests also use it as an in-process server.
/// </summary>
public sealed class McpServer
{
    private readonly string _name;
    private readonly string _version;
    private readonly List<(string Name, string Description, Delegate Function)> _tools = [];

    public McpServer(string name, string version = "1.0.0")
    {
        _name = name;
        _version = version;
    }

    /// <summary>Offer a tool. Its input schema is read from the delegate's parameters.</summary>
    public void AddTool(string name, Delegate function, string? description = null)
    {
        description ??= function.Method.GetCustomAttribute<DescriptionAttribute>()?.Description ?? "";
        _tools.Add((name, description, function));
    }

    /// <summary>Serve on this process's standard input and output until the client disconnects.</summary>
    public Task RunStdioAsync(CancellationToken cancellationToken = default) =>
        RunAsync(Console.In, Console.Out, cancellationToken);

    /// <summary>Serve on any pair of streams until the input ends.</summary>
    public async Task RunAsync(TextReader input, TextWriter output, CancellationToken cancellationToken = default)
    {
        while (await input.ReadLineAsync(cancellationToken) is { } line)
        {
            if (string.IsNullOrWhiteSpace(line) || JsonNode.Parse(line) is not JsonObject request)
            {
                continue;
            }

            var id = request["id"]?.DeepClone();
            var method = request["method"]?.GetValue<string>() ?? "";
            if (id is null)
            {
                continue; // notifications get no response
            }

            JsonObject response;
            try
            {
                var result = await HandleAsync(method, request["params"] as JsonObject, cancellationToken);
                response = new JsonObject { ["jsonrpc"] = "2.0", ["id"] = id, ["result"] = result };
            }
            catch (MissingMethodException)
            {
                response = Error(id, -32601, $"Method not found: {method}");
            }
            catch (Exception ex) when (ex is not OperationCanceledException)
            {
                response = Error(id, -32603, ex.Message);
            }

            await output.WriteLineAsync(response.ToJsonString().AsMemory(), cancellationToken);
            await output.FlushAsync(cancellationToken);
        }
    }

    private async Task<JsonNode> HandleAsync(string method, JsonObject? parameters, CancellationToken cancellationToken)
    {
        switch (method)
        {
            case "initialize":
                return new JsonObject
                {
                    ["protocolVersion"] = parameters?["protocolVersion"]?.GetValue<string>() ?? McpClient.ProtocolVersion,
                    ["capabilities"] = new JsonObject { ["tools"] = new JsonObject() },
                    ["serverInfo"] = new JsonObject { ["name"] = _name, ["version"] = _version },
                };

            case "ping":
                return new JsonObject();

            case "tools/list":
                var list = new JsonArray();
                foreach (var (name, description, function) in _tools)
                {
                    list.Add(new JsonObject
                    {
                        ["name"] = name,
                        ["description"] = description,
                        ["inputSchema"] = InputSchema(function),
                    });
                }
                return new JsonObject { ["tools"] = list };

            case "tools/call":
                var toolName = parameters?["name"]?.GetValue<string>() ?? "";
                var tool = _tools.FirstOrDefault(t => t.Name == toolName);
                if (tool.Function is null)
                {
                    return ToolResult($"Unknown tool: {toolName}", isError: true);
                }
                try
                {
                    var value = await ToolInvoker.InvokeAsync(tool.Function, parameters?["arguments"], cancellationToken);
                    return ToolResult(ToolInvoker.Format(value), isError: false);
                }
                catch (Exception ex) when (ex is not OperationCanceledException)
                {
                    return ToolResult(ex.Message, isError: true);
                }

            default:
                throw new MissingMethodException(method);
        }
    }

    private static JsonObject ToolResult(string text, bool isError) => new()
    {
        ["content"] = new JsonArray(new JsonObject { ["type"] = "text", ["text"] = text }),
        ["isError"] = isError,
    };

    private static JsonObject Error(JsonNode id, int code, string message) => new()
    {
        ["jsonrpc"] = "2.0",
        ["id"] = id,
        ["error"] = new JsonObject { ["code"] = code, ["message"] = message },
    };

    // Kept separate from ToolSchema so the server works before you've built chapter 5's native tools.
    private static JsonObject InputSchema(Delegate function)
    {
        var properties = new JsonObject();
        var required = new JsonArray();
        foreach (var parameter in function.Method.GetParameters())
        {
            if (parameter.ParameterType == typeof(CancellationToken))
            {
                continue;
            }
            var type = parameter.ParameterType;
            var jsonType = type == typeof(string) ? "string"
                : type == typeof(bool) ? "boolean"
                : type == typeof(int) || type == typeof(long) ? "integer"
                : type == typeof(double) || type == typeof(float) || type == typeof(decimal) ? "number"
                : "object";
            properties[parameter.Name!] = new JsonObject { ["type"] = jsonType };
            if (!parameter.HasDefaultValue)
            {
                required.Add(parameter.Name!);
            }
        }
        return new JsonObject { ["type"] = "object", ["properties"] = properties, ["required"] = required };
    }
}
