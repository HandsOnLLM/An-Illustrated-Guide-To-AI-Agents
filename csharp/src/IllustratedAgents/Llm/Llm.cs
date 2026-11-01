using System.Net.Http.Headers;
using System.Text;
using System.Text.Json.Nodes;

namespace IllustratedAgents;

/// <summary>
/// A wrapper around any OpenAI-compatible <c>/chat/completions</c> endpoint: Ollama, llama.cpp,
/// LM Studio, vLLM, OpenRouter. Chapter 2.
/// </summary>
public sealed class Llm : ILlm
{
    // One HttpClient for the whole process: creating one per call exhausts sockets under load.
    private static readonly HttpClient SharedHttp = new() { Timeout = TimeSpan.FromMinutes(10) };

    private readonly HttpClient _http;

    public Llm(
        string model,
        string baseUrl = "http://localhost:11434/v1",
        string apiKey = "no_key",
        bool think = false,
        double? temperature = null,
        HttpClient? httpClient = null)
    {
        Model = model;
        BaseUrl = baseUrl.TrimEnd('/');
        ApiKey = apiKey;
        Think = think;
        Temperature = temperature;
        _http = httpClient ?? SharedHttp;
    }

    public string Model { get; }
    public string BaseUrl { get; }
    public string ApiKey { get; }
    public bool Think { get; }
    public double? Temperature { get; }

    /// <summary>
    /// Builds an <see cref="Llm"/> from environment variables so the chapter demos run against
    /// whatever you have locally without editing code: <c>TINYAGENT_MODEL</c>,
    /// <c>TINYAGENT_BASE_URL</c> and <c>TINYAGENT_API_KEY</c>.
    /// </summary>
    public static Llm FromEnvironment(string defaultModel, bool think = false, double? temperature = null) =>
        new(
            model: Environment.GetEnvironmentVariable("TINYAGENT_MODEL") ?? defaultModel,
            baseUrl: Environment.GetEnvironmentVariable("TINYAGENT_BASE_URL") ?? "http://localhost:11434/v1",
            apiKey: Environment.GetEnvironmentVariable("TINYAGENT_API_KEY") ?? "no_key",
            think: think,
            temperature: temperature);

    public async Task<Response> GenerateAsync(
        IReadOnlyList<ChatMessage> messages,
        JsonArray? tools = null,
        CancellationToken cancellationToken = default)
    {
        // Build the request body
        var body = new JsonObject
        {
            ["model"] = Model,
            ["messages"] = new JsonArray(messages.Select(m => (JsonNode)ToJson(m)).ToArray()),
        };

        // Tools and reasoning
        if (tools is { Count: > 0 })
        {
            body["tools"] = tools.DeepClone();
        }
        body["reasoning_effort"] = Think ? "medium" : "none";
        if (Temperature is not null)
        {
            body["temperature"] = Temperature.Value;
        }

        // POST to the OpenAI-compatible /chat/completions endpoint
        using var request = new HttpRequestMessage(HttpMethod.Post, $"{BaseUrl}/chat/completions")
        {
            Content = new StringContent(body.ToJsonString(), Encoding.UTF8, "application/json"),
        };
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", ApiKey);

        using var httpResponse = await _http.SendAsync(request, cancellationToken);
        var text = await httpResponse.Content.ReadAsStringAsync(cancellationToken);
        if (!httpResponse.IsSuccessStatusCode)
        {
            throw new HttpRequestException(
                $"The model server returned {(int)httpResponse.StatusCode}: {text}");
        }

        var data = JsonNode.Parse(text)!.AsObject();

        // Extract message, tool call and metadata
        var message = data["choices"]![0]!["message"]!.AsObject();
        var reasoning = message["reasoning"]?.GetValue<string>() ?? message["reasoning_content"]?.GetValue<string>();
        var toolCalls = message["tool_calls"] as JsonArray;
        var toolCall = toolCalls is { Count: > 0 } ? toolCalls[0]!.DeepClone().AsObject() : null;
        var usage = data["usage"];
        var metadata = new ResponseMetadata(
            Model: data["model"]?.GetValue<string>() ?? Model,
            PromptTokens: usage?["prompt_tokens"]?.GetValue<int>() ?? 0,
            CompletionTokens: usage?["completion_tokens"]?.GetValue<int>() ?? 0);

        // Format as a Response
        return new Response
        {
            Content = message["content"]?.GetValue<string>() ?? "",
            Reasoning = reasoning,
            ToolCall = toolCall,
            Metadata = metadata,
        };
    }

    /// <summary>
    /// Turns a <see cref="ChatMessage"/> into the JSON shape the OpenAI-compatible API expects.
    /// Provided for you: it's plumbing, not an agent concept.
    /// </summary>
    public static JsonObject ToJson(ChatMessage message)
    {
        var json = new JsonObject { ["role"] = message.Role };

        if (message.Parts is { Count: > 0 } parts)
        {
            var content = new JsonArray();
            foreach (var part in parts)
            {
                content.Add(part.Type == "image_url"
                    ? new JsonObject { ["type"] = "image_url", ["image_url"] = new JsonObject { ["url"] = part.ImageUrl } }
                    : new JsonObject { ["type"] = "text", ["text"] = part.Text });
            }
            json["content"] = content;
        }
        else
        {
            json["content"] = message.Content;
        }

        if (message.ToolCall is not null)
        {
            // A JsonNode can only have one parent, so the stored tool call is copied, never moved.
            json["tool_calls"] = new JsonArray(message.ToolCall.DeepClone());
        }

        return json;
    }
}
