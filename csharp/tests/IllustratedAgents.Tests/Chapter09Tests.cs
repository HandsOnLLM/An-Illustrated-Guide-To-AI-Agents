namespace IllustratedAgents.Tests;

using TinyAgent = IllustratedAgents.Chapters.Ch09.TinyAgent;

public class Chapter09Tests
{
    [Fact]
    public async Task Multimodal_memory_stores_an_image_url_before_the_text()
    {
        var memory = new MultimodalMemory();

        await memory.AddAsync("user", "Which animal is on the cover?", imageData: "https://example.com/cover.png");

        var message = Assert.Single(memory.GetMessages());
        Assert.Equal(2, message.Parts!.Count);
        Assert.Equal(ContentPart.FromImageUrl("https://example.com/cover.png"), message.Parts[0]);
        Assert.Equal(ContentPart.FromText("Which animal is on the cover?"), message.Parts[1]);
    }

    [Fact]
    public async Task Multimodal_memory_turns_base64_into_a_data_url()
    {
        var memory = new MultimodalMemory();

        await memory.AddAsync("user", "PNG", imageData: "iVBORw0KGgoAAAANSUhEUg");
        await memory.AddAsync("user", "JPEG", imageData: "/9j/4AAQSkZJRgABAQ");

        Assert.Equal("data:image/png;base64,iVBORw0KGgoAAAANSUhEUg", memory.GetMessages()[0].Parts![0].ImageUrl);
        Assert.Equal("data:image/jpeg;base64,/9j/4AAQSkZJRgABAQ", memory.GetMessages()[1].Parts![0].ImageUrl);
    }

    [Fact]
    public async Task Multimodal_memory_without_an_image_stores_plain_text()
    {
        var memory = new MultimodalMemory();

        await memory.AddAsync("assistant", "A flamingo.");

        var message = Assert.Single(memory.GetMessages());
        Assert.Null(message.Parts);
        Assert.Equal("A flamingo.", message.Content);
    }

    [Fact]
    public void Image_messages_are_sent_as_a_content_array()
    {
        var message = new ChatMessage("user", "What is this?")
        {
            Parts = [ContentPart.FromImageUrl("https://example.com/a.png"), ContentPart.FromText("What is this?")],
        };

        var json = Llm.ToJson(message);

        var content = json["content"]!.AsArray();
        Assert.Equal("image_url", content[0]!["type"]!.GetValue<string>());
        Assert.Equal("https://example.com/a.png", content[0]!["image_url"]!["url"]!.GetValue<string>());
        Assert.Equal("What is this?", content[1]!["text"]!.GetValue<string>());
    }

    [Fact]
    public async Task Agent_passes_the_image_to_memory()
    {
        var llm = new FakeLlm("A parrot.");
        var agent = new TinyAgent(llm, new MultimodalMemory(), new NativeTools(), new NativeReAct());

        var answer = await agent.RunAsync("Which animal is on the cover?", imageData: "https://example.com/cover.png");

        Assert.Equal("A parrot.", answer);
        var user = llm.Calls[0].Single(m => m.Role == "user");
        Assert.Equal("https://example.com/cover.png", user.Parts![0].ImageUrl);
    }

    [Fact]
    public async Task Agent_still_works_without_an_image()
    {
        var agent = new TinyAgent(new FakeLlm("Hello!"), new MultimodalMemory(), new NativeTools(), new NativeReAct());

        Assert.Equal("Hello!", await agent.RunAsync("Hi"));
    }
}
