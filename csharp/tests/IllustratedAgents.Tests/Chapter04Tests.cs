using System.Text.Json.Nodes;

namespace IllustratedAgents.Tests;

using TinyAgent = IllustratedAgents.Chapters.Ch04.TinyAgent;

public class Chapter04Tests
{
    [Fact]
    public async Task Memory_keeps_messages_in_order()
    {
        var memory = new Memory();

        await memory.AddAsync("user", "Hi!");
        await memory.AddAsync("assistant", "Hello!");

        var messages = memory.GetMessages();
        Assert.Equal(2, messages.Count);
        Assert.Equal(new ChatMessage("user", "Hi!"), messages[0]);
        Assert.Equal("assistant", messages[1].Role);
    }

    [Fact]
    public async Task Memory_stores_a_tool_call_with_its_message()
    {
        var memory = new Memory();
        var toolCall = new JsonObject { ["id"] = "call_1" };

        await memory.AddAsync("assistant", "", toolCall);

        Assert.Same(toolCall, memory.GetMessages()[0].ToolCall);
    }

    [Fact]
    public async Task Agent_with_memory_sees_the_earlier_conversation()
    {
        var llm = new FakeLlm("Nice to meet you!", "You are Maarten and Jay.");
        var agent = new TinyAgent(llm, new Memory());

        await agent.RunAsync("Hi! We are Maarten and Jay.");
        var answer = await agent.RunAsync("What are our names?");

        Assert.Equal("You are Maarten and Jay.", answer);
        var secondCall = llm.Calls[1];
        Assert.Equal(3, secondCall.Count);
        Assert.Equal("Hi! We are Maarten and Jay.", secondCall[0].Content);
        Assert.Equal("Nice to meet you!", secondCall[1].Content);
        Assert.Equal(4, agent.Memory.GetMessages().Count);
    }

    [Fact]
    public async Task TrimmingMemory_keeps_the_system_message_and_the_last_two_turns()
    {
        var memory = new TrimmingMemory();
        await memory.AddAsync("system", "Be brief.");
        for (var turn = 1; turn <= 4; turn++)
        {
            await memory.AddAsync("user", $"question {turn}");
            await memory.AddAsync("assistant", $"answer {turn}");
        }

        var messages = memory.GetMessages();

        Assert.Equal(5, messages.Count);
        Assert.Equal("Be brief.", messages[0].Content);
        Assert.Equal("question 3", messages[1].Content);
        Assert.Equal("answer 4", messages[4].Content);
    }

    [Fact]
    public async Task SummarizationMemory_folds_each_turn_into_one_system_message()
    {
        var llm = new FakeLlm("Sarah asked why flamingos are pink.");
        var memory = new SummarizationMemory(llm);

        await memory.AddAsync("user", "Hi, my name is Sarah. Why are flamingos pink?");
        Assert.Empty(llm.Calls); // nothing to summarize until the assistant replies
        await memory.AddAsync("assistant", "Their food contains pigments.");

        var message = Assert.Single(memory.GetMessages());
        Assert.Equal("system", message.Role);
        Assert.Equal("Sarah asked why flamingos are pink.", message.Content);

        var prompt = Assert.Single(Assert.Single(llm.Calls)).Content!;
        Assert.Contains("user: Hi, my name is Sarah. Why are flamingos pink?", prompt);
        Assert.Contains("assistant: Their food contains pigments.", prompt);
    }

    [Fact]
    public async Task SummarizationMemory_passes_the_previous_summary_along()
    {
        var llm = new FakeLlm("Summary one.", "Summary two.");
        var memory = new SummarizationMemory(llm);

        await memory.AddAsync("user", "first");
        await memory.AddAsync("assistant", "reply");
        await memory.AddAsync("user", "second");
        await memory.AddAsync("assistant", "reply");

        Assert.Contains("Summary: Summary one.", llm.Calls[1][0].Content);
        Assert.Equal("Summary two.", memory.GetMessages()[0].Content);
    }

    [Fact]
    public void Cosine_is_one_for_the_same_direction_and_zero_for_unrelated()
    {
        Assert.Equal(1.0, RagMemory.Cosine([1, 2, 3], [2, 4, 6]), 6);
        Assert.Equal(0.0, RagMemory.Cosine([1, 0], [0, 1]), 6);
    }

    private static readonly string[] Documents =
    [
        "Sarah lives in Lisbon, Portugal.",
        "Sarah's favorite animals are flamingos.",
        "Ilse plays the cello in a local string quartet.",
        "Ilse's favorite animals are dolphins.",
    ];

    [Fact]
    public async Task RagMemory_embeds_every_document_once()
    {
        var embedder = new FakeEmbeddingModel();

        var memory = await RagMemory.CreateAsync(embedder, Documents);

        Assert.Equal(Documents.Length, memory.Embeddings.Count);
        Assert.Equal(Documents.Length, embedder.Calls);
    }

    [Fact]
    public async Task RagMemory_finds_the_most_similar_documents_first()
    {
        var memory = await RagMemory.CreateAsync(new FakeEmbeddingModel(), Documents);

        var results = await memory.SearchAsync("What is Sarah's favorite animal?", k: 2);

        Assert.Equal(2, results.Count);
        Assert.Equal("Sarah's favorite animals are flamingos.", results[0]);
    }

    [Fact]
    public async Task RagMemory_adds_retrieved_context_to_user_messages_only()
    {
        var memory = await RagMemory.CreateAsync(new FakeEmbeddingModel(), Documents);

        await memory.AddAsync("user", "What is Sarah's favorite animal?");
        await memory.AddAsync("assistant", "Flamingos.");

        var user = memory.GetMessages()[0].Content!;
        Assert.StartsWith("Context:\n", user);
        Assert.Contains("Sarah's favorite animals are flamingos.", user);
        Assert.EndsWith("Question: What is Sarah's favorite animal?", user);
        Assert.Equal("Flamingos.", memory.GetMessages()[1].Content);
    }

    [Fact]
    public async Task EmbeddingModel_posts_to_embeddings_and_returns_the_vector()
    {
        var http = new FakeHttpHandler("""{ "data": [ { "embedding": [0.5, -1, 2] } ] }""");
        var model = new EmbeddingModel("embeddinggemma", httpClient: new HttpClient(http));

        var vector = await model.EmbedAsync("Dolphins are amazing!");

        Assert.Equal(new[] { 0.5f, -1f, 2f }, vector);
        Assert.Equal("http://localhost:11434/v1/embeddings", http.Request!.RequestUri!.ToString());
        Assert.Equal("Dolphins are amazing!", http.RequestJson["input"]!.GetValue<string>());
        Assert.Equal("embeddinggemma", http.RequestJson["model"]!.GetValue<string>());
    }
}
