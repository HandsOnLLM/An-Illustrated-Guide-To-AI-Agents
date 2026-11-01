using System.Text.Json.Nodes;

namespace IllustratedAgents.Tests;

public class Chapter10Tests
{
    [Fact]
    public void SafePath_allows_paths_inside_the_workspace()
    {
        using var folder = new TempFolder();
        var tools = new CodeTools(folder.Path);

        Assert.Equal(Path.Combine(tools.Root, "src", "app.cs"), tools.SafePath("src/app.cs"));
        Assert.Equal(tools.Root, tools.SafePath("."));
    }

    [Theory]
    [InlineData("../secrets.txt")]
    [InlineData("src/../../escape.txt")]
    [InlineData("/etc/passwd")]
    public void SafePath_rejects_paths_outside_the_workspace(string path)
    {
        using var folder = new TempFolder();

        Assert.Throws<UnauthorizedAccessException>(() => new CodeTools(folder.Path).SafePath(path));
    }

    [Fact]
    public void SafePath_rejects_a_sibling_folder_that_shares_the_name_prefix()
    {
        using var folder = new TempFolder();
        var tools = new CodeTools(Path.Combine(folder.Path, "work"));

        Assert.Throws<UnauthorizedAccessException>(() => tools.SafePath("../work-other/file.txt"));
    }

    [Fact]
    public void Files_can_be_written_listed_and_read_back()
    {
        using var folder = new TempFolder();
        var tools = new CodeTools(folder.Path);

        Assert.Equal("Written to 'notes/hello.txt'.", tools.WriteFile("notes/hello.txt", "Hi!"));
        Assert.Equal("Hi!", tools.ReadFile("notes/hello.txt"));
        Assert.Equal("notes/", tools.ListFiles("."));
        Assert.Equal("hello.txt", tools.ListFiles("notes"));
    }

    [Fact]
    public void Missing_files_and_folders_are_reported_not_thrown()
    {
        using var folder = new TempFolder();
        var tools = new CodeTools(folder.Path);

        Assert.Equal("Error: 'nope.txt' not found.", tools.ReadFile("nope.txt"));
        Assert.Equal("Error: 'nope' is not a directory.", tools.ListFiles("nope"));
        Assert.Equal("(empty)", tools.ListFiles());
    }

    [Fact]
    public async Task Writing_and_running_code_need_approval()
    {
        using var folder = new TempFolder();
        var codeTools = new CodeTools(folder.Path);
        var registry = codeTools.CreateRegistry(approve: _ => false);

        var result = await registry.ExecuteAsync(new Response
        {
            ToolCall = new JsonObject { ["tool"] = "write_file", ["kwargs"] = new JsonObject { ["path"] = "x.txt", ["content"] = "hi" } },
        });

        Assert.Equal("Tool 'write_file' was denied by the user.", result);
        Assert.False(File.Exists(Path.Combine(folder.Path, "x.txt")));
        Assert.True(registry.RequiresApproval.SetEquals(["write_file", "run_csharp"]));
        Assert.Equal(new[] { "read_file", "list_files", "write_file", "run_csharp" }, registry.Registry.Keys);
    }

    [Fact]
    public async Task A_path_escape_through_the_agent_becomes_an_error_message()
    {
        using var folder = new TempFolder();
        var registry = new CodeTools(folder.Path).CreateRegistry();

        var result = await registry.ExecuteAsync(new Response
        {
            ToolCall = new JsonObject { ["tool"] = "read_file", ["kwargs"] = new JsonObject { ["path"] = "../../etc/passwd" } },
        });

        Assert.Contains("outside the workspace", Assert.IsType<string>(result));
    }

    [Fact]
    public async Task Agent_tells_the_display_each_event_in_order()
    {
        var display = new RecordingDisplay();
        var tools = new NativeTools();
        tools.AddTool("multiply", Toolbox.Multiply);
        var llm = new FakeLlm().ThenToolCall("multiply", """{"a": "6", "b": "7"}""").Then("42");
        var agent = new TinyAgent(llm, new Memory(), tools, new NativeReAct(), display);

        var answer = await agent.RunAsync("What is 6 times 7?");

        Assert.Equal("42", answer);
        Assert.Equal(
            new[] { "thinking", "response", "tool_call", "observation", "thinking", "response" },
            display.Events);
    }

    [Fact]
    public async Task Agent_without_a_display_stays_quiet()
    {
        var agent = new TinyAgent(new FakeLlm("Hi!"), new Memory(), new NativeTools(), new NativeReAct());

        Assert.Equal("Hi!", await agent.RunAsync("Hello"));
        Assert.IsType<Display>(agent.Display);
    }

    [Fact]
    public async Task Agent_accepts_an_image_like_chapter_9()
    {
        var llm = new FakeLlm("A flamingo.");
        var agent = new TinyAgent(llm, new MultimodalMemory(), new NativeTools(), new NativeReAct());

        await agent.RunAsync("What is this?", imageData: "https://example.com/bird.png");

        Assert.NotNull(llm.Calls[0].Single(m => m.Role == "user").Parts);
    }
}
