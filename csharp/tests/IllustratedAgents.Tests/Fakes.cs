using System.Net;
using System.Text;
using System.Text.Json.Nodes;

namespace IllustratedAgents.Tests;

/// <summary>
/// A model that replies from a script instead of thinking, so the tests are fast, free and repeatable.
/// It also records every conversation it was sent.
/// </summary>
public sealed class FakeLlm : ILlm
{
    private readonly Queue<Func<Response>> _script = new();

    public FakeLlm(params string[] replies)
    {
        foreach (var reply in replies)
        {
            Then(reply);
        }
    }

    /// <summary>Every conversation the model was sent, as a snapshot taken at call time.</summary>
    public List<List<ChatMessage>> Calls { get; } = [];

    /// <summary>The native tool schemas sent with each call (null when none).</summary>
    public List<JsonArray?> ToolsSent { get; } = [];

    public FakeLlm Then(string content, string? reasoning = null)
    {
        _script.Enqueue(() => new Response { Content = content, Reasoning = reasoning });
        return this;
    }

    /// <summary>Script a native tool call, shaped like the OpenAI API returns it.</summary>
    public FakeLlm ThenToolCall(string name, string argumentsJson, string? reasoning = null)
    {
        _script.Enqueue(() => new Response
        {
            Reasoning = reasoning,
            ToolCall = new JsonObject
            {
                ["id"] = "call_1",
                ["type"] = "function",
                ["function"] = new JsonObject { ["name"] = name, ["arguments"] = argumentsJson },
            },
        });
        return this;
    }

    public Task<Response> GenerateAsync(IReadOnlyList<ChatMessage> messages, JsonArray? tools = null, CancellationToken cancellationToken = default)
    {
        Calls.Add(messages.ToList());
        ToolsSent.Add(tools?.DeepClone().AsArray());
        if (_script.Count == 0)
        {
            throw new InvalidOperationException("FakeLlm ran out of scripted replies.");
        }
        return Task.FromResult(_script.Dequeue()());
    }
}

/// <summary>
/// Embeds text as word counts over a fixed vocabulary: crude, but texts that share words point the same way,
/// which is all a retrieval test needs.
/// </summary>
public sealed class FakeEmbeddingModel : IEmbeddingModel
{
    private static readonly string[] Vocabulary = ["sarah", "ilse", "flamingos", "dolphins", "lisbon", "amsterdam", "cello", "climbing", "animal", "animals", "favorite"];

    public int Calls { get; private set; }

    public Task<float[]> EmbedAsync(string text, CancellationToken cancellationToken = default)
    {
        Calls++;
        var words = text.ToLowerInvariant().Split([' ', '.', ',', '?', '\'', '!'], StringSplitOptions.RemoveEmptyEntries);
        var vector = Vocabulary.Select(term => (float)words.Count(word => word.StartsWith(term))).ToArray();
        return Task.FromResult(vector);
    }
}

/// <summary>Stands in for the network: records the request and returns a canned reply.</summary>
public sealed class FakeHttpHandler(string responseJson, HttpStatusCode status = HttpStatusCode.OK) : HttpMessageHandler
{
    public HttpRequestMessage? Request { get; private set; }
    public string? RequestBody { get; private set; }

    public JsonObject RequestJson => JsonNode.Parse(RequestBody!)!.AsObject();

    protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        Request = request;
        RequestBody = request.Content is null ? null : await request.Content.ReadAsStringAsync(cancellationToken);
        return new HttpResponseMessage(status) { Content = new StringContent(responseJson, Encoding.UTF8, "application/json") };
    }
}

/// <summary>An agent that answers every task with the same text and remembers what it was asked.</summary>
public sealed class StubAgent(string answer) : IAgent
{
    public List<string> Tasks { get; } = [];
    public Trajectory Trajectory { get; } = new();

    public Task<string> RunAsync(string task, CancellationToken cancellationToken = default)
    {
        Tasks.Add(task);
        return Task.FromResult(answer);
    }
}

/// <summary>Writes down every display event in order.</summary>
public sealed class RecordingDisplay : Display
{
    public List<string> Events { get; } = [];

    public override void Thinking() => Events.Add("thinking");
    public override void ShowResponse(Response response) => Events.Add("response");
    public override void ShowToolCall(Response response) => Events.Add("tool_call");
    public override void ShowObservation(string observation) => Events.Add("observation");
}

/// <summary>A temporary folder that deletes itself.</summary>
public sealed class TempFolder : IDisposable
{
    public TempFolder()
    {
        Path = System.IO.Path.Combine(System.IO.Path.GetTempPath(), "tinyagent-tests-" + Guid.NewGuid().ToString("N")[..8]);
        Directory.CreateDirectory(Path);
    }

    public string Path { get; }

    public void Dispose()
    {
        try { Directory.Delete(Path, recursive: true); } catch (IOException) { }
    }
}
