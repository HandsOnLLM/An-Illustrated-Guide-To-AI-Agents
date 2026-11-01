using System.Text.Json.Nodes;

namespace IllustratedAgents;

/// <summary>Memory that can store an image alongside a message. Chapter 9.</summary>
public class MultimodalMemory : Memory
{
    public override Task AddAsync(
        string role,
        string? content,
        JsonObject? toolCall = null,
        string? imageData = null,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrEmpty(imageData))
        {
            return base.AddAsync(role, content, toolCall, imageData, cancellationToken);
        }

        // A web address is passed through; raw base64 becomes a data URL
        var url = imageData.StartsWith("http://") || imageData.StartsWith("https://")
            ? imageData
            : $"data:{GuessMimeType(imageData)};base64,{imageData}";

        Messages.Add(new ChatMessage(role, content)
        {
            Parts = [ContentPart.FromImageUrl(url), ContentPart.FromText(content ?? "")],
            ToolCall = toolCall,
        });
        return Task.CompletedTask;
    }

    /// <summary>PNG files start with the bytes that encode to "iVBOR"; everything else is treated as JPEG.</summary>
    private static string GuessMimeType(string base64) =>
        base64.StartsWith("iVBOR") ? "image/png" : "image/jpeg";
}
