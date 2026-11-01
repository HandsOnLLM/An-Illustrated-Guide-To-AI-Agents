using System.Text;
using System.Text.Json.Nodes;

namespace IllustratedAgents;

/// <summary>
/// Turns text into an embedding through any OpenAI-compatible <c>/embeddings</c> endpoint. Chapter 4.
/// </summary>
public sealed class EmbeddingModel : IEmbeddingModel
{
    private static readonly HttpClient SharedHttp = new() { Timeout = TimeSpan.FromMinutes(5) };

    private readonly HttpClient _http;

    public EmbeddingModel(string model, string baseUrl = "http://localhost:11434/v1", HttpClient? httpClient = null)
    {
        Model = model;
        BaseUrl = baseUrl.TrimEnd('/');
        _http = httpClient ?? SharedHttp;
    }

    public string Model { get; }
    public string BaseUrl { get; }

    public async Task<float[]> EmbedAsync(string text, CancellationToken cancellationToken = default)
    {
        // POST to the OpenAI-compatible /embeddings endpoint
        var body = new JsonObject { ["model"] = Model, ["input"] = text };
        using var content = new StringContent(body.ToJsonString(), Encoding.UTF8, "application/json");
        using var httpResponse = await _http.PostAsync($"{BaseUrl}/embeddings", content, cancellationToken);
        var json = await httpResponse.Content.ReadAsStringAsync(cancellationToken);
        if (!httpResponse.IsSuccessStatusCode)
        {
            throw new HttpRequestException($"The embedding server returned {(int)httpResponse.StatusCode}: {json}");
        }

        // Extract and return the embedding
        var vector = JsonNode.Parse(json)!["data"]![0]!["embedding"]!.AsArray();
        return vector.Select(v => v!.GetValue<float>()).ToArray();
    }
}
