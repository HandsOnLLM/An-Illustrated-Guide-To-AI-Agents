using System.Text;
using System.Text.Json.Nodes;

namespace IllustratedAgents;

/// <summary>
/// Short-term memory that compresses the conversation into a running summary after every assistant
/// message. The summary lives in a single system message. Chapter 4.
/// </summary>
public class SummarizationMemory : Memory
{
    private readonly ILlm _llm;

    public SummarizationMemory(ILlm llm) => _llm = llm;

    public override async Task AddAsync(
        string role,
        string? content,
        JsonObject? toolCall = null,
        string? imageData = null,
        CancellationToken cancellationToken = default)
    {
        // Add the new message first, using the base class
        await base.AddAsync(role, content, toolCall, imageData, cancellationToken);

        // After each completed turn, update the running summary
        if (role != "assistant")
        {
            return;
        }

        // Split the existing summary from the new conversation turns
        var summary = "";
        var conversation = new StringBuilder();
        foreach (var message in Messages)
        {
            if (message.Role == "system")
            {
                summary = message.Content ?? "";
            }
            else
            {
                conversation.Append($"{message.Role}: {message.Content}\n");
            }
        }

        // Ask the model to extend the summary with the new conversation
        var prompt = $"""
            Update the summary with the new conversation.

            Summary: {summary}

            Conversation:
            {conversation}
            Output the updated summary only.
            """;
        var response = await _llm.GenerateAsync([new ChatMessage("user", prompt)], cancellationToken: cancellationToken);
        Messages = [new ChatMessage("system", response.Content)];
    }
}
