using System.Diagnostics;
using System.Text.Json.Nodes;

namespace IllustratedAgents;

/// <summary>A tool an MCP server offers.</summary>
public sealed record McpToolInfo(string Name, string? Description, JsonObject? InputSchema);

/// <summary>An error an MCP server returned.</summary>
public sealed class McpException(string message) : Exception(message);

/// <summary>
/// A minimal Model Context Protocol client over the stdio transport: newline-delimited JSON-RPC 2.0
/// messages on a server process's standard input and output. Chapter 5.
/// </summary>
/// <remarks>
/// The Python version uses the official <c>mcp</c> package. This one is written by hand so you can see the
/// protocol: <c>initialize</c>, then <c>notifications/initialized</c>, then <c>tools/list</c> and
/// <c>tools/call</c>. AI Foundations Phase 8 replaces it with the official MCP C# SDK.
/// </remarks>
public sealed class McpClient : IAsyncDisposable
{
    public const string ProtocolVersion = "2025-06-18";

    private readonly TextReader _fromServer;
    private readonly TextWriter _toServer;
    private readonly Process? _process;
    private readonly SemaphoreSlim _gate = new(1, 1);
    private int _nextId;

    /// <summary>Talk to a server over any pair of streams. Tests use in-memory pipes.</summary>
    public McpClient(TextReader fromServer, TextWriter toServer, Process? process = null)
    {
        _fromServer = fromServer;
        _toServer = toServer;
        _process = process;
    }

    /// <summary>The server's name and version, from the initialize handshake.</summary>
    public JsonObject? ServerInfo { get; private set; }

    /// <summary>Start a server process, connect to its stdio, and run the initialize handshake.</summary>
    public static async Task<McpClient> StartAsync(string command, IEnumerable<string> arguments, CancellationToken cancellationToken = default)
    {
        var startInfo = new ProcessStartInfo(command)
        {
            RedirectStandardInput = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
        };
        foreach (var argument in arguments)
        {
            startInfo.ArgumentList.Add(argument);
        }

        var process = Process.Start(startInfo) ?? throw new InvalidOperationException($"Could not start '{command}'.");

        // Drain stderr so a chatty server can never block on a full pipe.
        _ = Task.Run(() => process.StandardError.ReadToEndAsync(), CancellationToken.None);

        var client = new McpClient(process.StandardOutput, process.StandardInput, process);
        await client.InitializeAsync(cancellationToken);
        return client;
    }

    /// <summary>The handshake: agree on a protocol version, then confirm with a notification.</summary>
    public async Task InitializeAsync(CancellationToken cancellationToken = default)
    {
        var result = await RequestAsync("initialize", new JsonObject
        {
            ["protocolVersion"] = ProtocolVersion,
            ["capabilities"] = new JsonObject(),
            ["clientInfo"] = new JsonObject { ["name"] = "TinyAgent", ["version"] = "1.0.0" },
        }, cancellationToken);

        ServerInfo = result?["serverInfo"]?.DeepClone().AsObject();
        await NotifyAsync("notifications/initialized", cancellationToken);
    }

    /// <summary>Ask the server which tools it offers.</summary>
    public async Task<IReadOnlyList<McpToolInfo>> ListToolsAsync(CancellationToken cancellationToken = default)
    {
        var result = await RequestAsync("tools/list", new JsonObject(), cancellationToken);
        var tools = result?["tools"] as JsonArray ?? [];
        return tools
            .OfType<JsonObject>()
            .Select(tool => new McpToolInfo(
                Name: tool["name"]!.GetValue<string>(),
                Description: tool["description"]?.GetValue<string>(),
                InputSchema: tool["inputSchema"]?.DeepClone().AsObject()))
            .ToList();
    }

    /// <summary>Call one tool and return the text of its first content block.</summary>
    public async Task<string> CallToolAsync(string name, JsonObject arguments, CancellationToken cancellationToken = default)
    {
        var result = await RequestAsync("tools/call", new JsonObject
        {
            ["name"] = name,
            ["arguments"] = arguments.DeepClone(),
        }, cancellationToken);

        var text = result?["content"]?[0]?["text"]?.GetValue<string>() ?? "";
        var isError = result?["isError"]?.GetValue<bool>() ?? false;
        return isError ? $"Error: {text}" : text;
    }

    /// <summary>
    /// Send one JSON-RPC request and wait for the response with the same id, skipping any notifications
    /// the server sends in between. Provided for you.
    /// </summary>
    public async Task<JsonNode?> RequestAsync(string method, JsonObject? parameters, CancellationToken cancellationToken = default)
    {
        await _gate.WaitAsync(cancellationToken);
        try
        {
            var id = Interlocked.Increment(ref _nextId);
            var request = new JsonObject { ["jsonrpc"] = "2.0", ["id"] = id, ["method"] = method };
            if (parameters is not null)
            {
                request["params"] = parameters;
            }
            await WriteAsync(request, cancellationToken);

            while (true)
            {
                var line = await _fromServer.ReadLineAsync(cancellationToken)
                    ?? throw new McpException($"The server closed the connection during '{method}'.");
                if (string.IsNullOrWhiteSpace(line) || JsonNode.Parse(line) is not JsonObject message)
                {
                    continue;
                }
                if (message["id"]?.ToJsonString() != id.ToString())
                {
                    continue; // a notification or log line, not our answer
                }
                if (message["error"] is JsonObject error)
                {
                    throw new McpException(error["message"]?.GetValue<string>() ?? "Unknown MCP error.");
                }
                return message["result"];
            }
        }
        finally
        {
            _gate.Release();
        }
    }

    /// <summary>Send a notification: a message with no id, which gets no response. Provided for you.</summary>
    public Task NotifyAsync(string method, CancellationToken cancellationToken = default) =>
        WriteAsync(new JsonObject { ["jsonrpc"] = "2.0", ["method"] = method }, cancellationToken);

    private async Task WriteAsync(JsonObject message, CancellationToken cancellationToken)
    {
        await _toServer.WriteLineAsync(message.ToJsonString().AsMemory(), cancellationToken);
        await _toServer.FlushAsync(cancellationToken);
    }

    public async ValueTask DisposeAsync()
    {
        _toServer.Dispose();
        if (_process is { HasExited: false })
        {
            try
            {
                await _process.WaitForExitAsync(new CancellationTokenSource(TimeSpan.FromSeconds(2)).Token);
            }
            catch (OperationCanceledException)
            {
                _process.Kill(entireProcessTree: true);
            }
        }
        _process?.Dispose();
        _gate.Dispose();
    }
}
