using System.ComponentModel;
using System.IO.Pipes;
using System.Text.Json.Nodes;

namespace IllustratedAgents.Tests;

using TinyAgent = IllustratedAgents.Chapters.Ch05.TinyAgent;

public class Chapter05Tests
{
    private static Tools MathTools(IEnumerable<string>? requiresApproval = null, Func<string, bool>? approve = null)
    {
        var tools = new Tools(requiresApproval, approve);
        tools.AddTool("multiply", Toolbox.Multiply, "Multiplies two numbers: multiply(a: str, b: str)");
        tools.AddTool("get_weather", Toolbox.GetWeather, "Gets weather: get_weather(location: str)");
        return tools;
    }

    private static Response Call(string tool, JsonNode? kwargs) =>
        new() { ToolCall = new JsonObject { ["tool"] = tool, ["kwargs"] = kwargs } };

    // ---- Text-based tools ----

    [Fact]
    public void AddTool_registers_tools_in_order()
    {
        var tools = MathTools();

        Assert.Equal(new[] { "multiply", "get_weather" }, tools.Registry.Keys);
        Assert.Equal("Multiplies two numbers: multiply(a: str, b: str)", tools.Registry["multiply"].Description);
    }

    [Fact]
    public void Descriptions_lists_one_tool_per_line()
    {
        Assert.Equal(
            "`multiply`: Multiplies two numbers: multiply(a: str, b: str)\n`get_weather`: Gets weather: get_weather(location: str)",
            MathTools().Descriptions);
    }

    [Fact]
    public void Prompt_names_the_tools_and_the_json_format()
    {
        var prompt = MathTools().Prompt;

        Assert.Contains("# Tools", prompt);
        Assert.Contains("`multiply`: Multiplies two numbers", prompt);
        Assert.Contains("""{"tool": "name", "kwargs": {"param": "value"}}""", prompt);
    }

    [Fact]
    public void Parse_extracts_a_json_tool_call_from_text()
    {
        var response = new Response { Content = """Sure! {"tool": "multiply", "kwargs": {"a": "5.1", "b": "7.3"}} Done.""" };

        var parsed = MathTools().Parse(response);

        Assert.Equal("multiply", parsed.ToolCall!["tool"]!.GetValue<string>());
        Assert.Equal("5.1", parsed.ToolCall["kwargs"]!["a"]!.GetValue<string>());
        Assert.Equal(response.Content, parsed.Content);
    }

    [Fact]
    public void Parse_tolerates_a_trailing_comma()
    {
        var response = new Response { Content = "{\n \"tool\": \"get_weather\",\n \"kwargs\": {\"location\": \"Lisbon\"},\n}" };

        Assert.NotNull(MathTools().Parse(response).ToolCall);
    }

    [Fact]
    public void Parse_leaves_plain_text_alone()
    {
        var response = new Response { Content = "Flamingos are pink because of their food." };

        Assert.Null(MathTools().Parse(response).ToolCall);
    }

    [Fact]
    public async Task ExecuteAsync_runs_the_tool_with_its_arguments()
    {
        var result = await MathTools().ExecuteAsync(Call("multiply", new JsonObject { ["a"] = "5.1", ["b"] = "7.3" }));

        Assert.Equal(37.23, Assert.IsType<double>(result), 6);
    }

    [Fact]
    public async Task ExecuteAsync_accepts_numbers_for_string_parameters()
    {
        var result = await MathTools().ExecuteAsync(Call("multiply", JsonNode.Parse("""{"a": 2, "b": 3}""")));

        Assert.Equal(6.0, result);
    }

    [Fact]
    public async Task ExecuteAsync_reports_an_unknown_tool()
    {
        Assert.Equal("Tool 'teleport' not found.", await MathTools().ExecuteAsync(Call("teleport", new JsonObject())));
    }

    [Fact]
    public async Task ExecuteAsync_asks_before_running_a_tool_that_needs_approval()
    {
        var asked = new List<string>();
        var tools = MathTools(requiresApproval: ["multiply"], approve: name => { asked.Add(name); return false; });

        var result = await tools.ExecuteAsync(Call("multiply", new JsonObject { ["a"] = "2", ["b"] = "3" }));

        Assert.Equal("Tool 'multiply' was denied by the user.", result);
        Assert.Equal(new[] { "multiply" }, asked);
    }

    [Fact]
    public async Task ExecuteAsync_runs_an_approved_tool_and_skips_approval_for_others()
    {
        var asked = 0;
        var tools = MathTools(requiresApproval: ["multiply"], approve: _ => { asked++; return true; });

        Assert.Equal(6.0, await tools.ExecuteAsync(Call("multiply", new JsonObject { ["a"] = "2", ["b"] = "3" })));
        await tools.ExecuteAsync(Call("get_weather", new JsonObject { ["location"] = "Lisbon" }));

        Assert.Equal(1, asked);
    }

    [Fact]
    public async Task ExecuteAsync_turns_a_failing_tool_into_a_message()
    {
        var result = await MathTools().ExecuteAsync(Call("multiply", new JsonObject { ["a"] = "five", ["b"] = "7" }));

        Assert.StartsWith("Error running tool 'multiply':", Assert.IsType<string>(result));
    }

    [Fact]
    public async Task ExecuteAsync_awaits_async_tools()
    {
        var tools = new Tools();
        Func<string, Task<string>> shout = async text => { await Task.Yield(); return text.ToUpperInvariant(); };
        tools.AddTool("shout", shout);

        Assert.Equal("HI", await tools.ExecuteAsync(Call("shout", new JsonObject { ["text"] = "hi" })));
    }

    [Fact]
    public void Observation_is_a_user_message_starting_with_OBSERVATION()
    {
        Assert.Equal(("user", "OBSERVATION: 37.23"), MathTools().Observation(37.23));
    }

    [Fact]
    public void IsDone_without_a_tool_call()
    {
        Assert.True(MathTools().IsDone(new Response { Content = "Hello!" }));
    }

    [Fact]
    public void IsDone_with_final_answer_uses_its_kwargs_as_the_answer()
    {
        var response = Call("final_answer", "37.23");

        Assert.True(MathTools().IsDone(response));
        Assert.Equal("37.23", response.Content);
    }

    [Fact]
    public void IsDone_unwraps_a_final_answer_wrapped_in_an_object()
    {
        var response = Call("final_answer", new JsonObject { ["answer"] = "Lisbon" });

        Assert.True(MathTools().IsDone(response));
        Assert.Equal("Lisbon", response.Content);
    }

    [Fact]
    public void IsDone_is_false_for_any_other_tool()
    {
        Assert.False(MathTools().IsDone(Call("multiply", new JsonObject())));
    }

    // ---- Native tool calling ----

    [Fact]
    public void ToolSchema_describes_a_function()
    {
        var schema = ToolSchema.FromDelegate("multiply", Toolbox.Multiply);

        Assert.Equal("function", schema["type"]!.GetValue<string>());
        var function = schema["function"]!;
        Assert.Equal("multiply", function["name"]!.GetValue<string>());
        Assert.Equal("Multiply two numbers.", function["description"]!.GetValue<string>());
        Assert.Equal("string", function["parameters"]!["properties"]!["a"]!["type"]!.GetValue<string>());
        Assert.Equal(new[] { "a", "b" }, function["parameters"]!["required"]!.AsArray().Select(n => n!.GetValue<string>()));
    }

    private static string Describe(int count, List<string> items, bool loud = false, double ratio = 1) => "";

    [Fact]
    public void ToolSchema_maps_types_and_skips_parameters_with_defaults()
    {
        var schema = ToolSchema.FromDelegate("describe", Describe, "fallback description");

        var function = schema["function"]!;
        var properties = function["parameters"]!["properties"]!;
        Assert.Equal("fallback description", function["description"]!.GetValue<string>());
        Assert.Equal("integer", properties["count"]!["type"]!.GetValue<string>());
        Assert.Equal("array", properties["items"]!["type"]!.GetValue<string>());
        Assert.Equal("boolean", properties["loud"]!["type"]!.GetValue<string>());
        Assert.Equal("number", properties["ratio"]!["type"]!.GetValue<string>());
        Assert.Equal(new[] { "count", "items" }, function["parameters"]!["required"]!.AsArray().Select(n => n!.GetValue<string>()));
    }

    [Fact]
    public void NativeTools_sends_schemas_and_no_prompt()
    {
        var tools = new NativeTools();
        tools.AddTool("multiply", Toolbox.Multiply);
        tools.AddTool("get_weather", Toolbox.GetWeather);

        Assert.Equal(2, tools.Schemas!.Count);
        Assert.Equal("", tools.Prompt);
    }

    [Fact]
    public void NativeTools_parses_string_arguments_into_kwargs()
    {
        var response = new Response
        {
            ToolCall = new JsonObject
            {
                ["function"] = new JsonObject { ["name"] = "multiply", ["arguments"] = """{"a": "5.1", "b": "7.3"}""" },
            },
        };

        var parsed = new NativeTools().Parse(response);

        Assert.Equal("multiply", parsed.ToolCall!["tool"]!.GetValue<string>());
        Assert.Equal("7.3", parsed.ToolCall["kwargs"]!["b"]!.GetValue<string>());
    }

    [Fact]
    public void NativeTools_parses_object_arguments_too()
    {
        var response = new Response
        {
            ToolCall = new JsonObject
            {
                ["function"] = new JsonObject { ["name"] = "get_weather", ["arguments"] = new JsonObject { ["location"] = "Lisbon" } },
            },
        };

        var parsed = new NativeTools().Parse(response);

        Assert.Equal("Lisbon", parsed.ToolCall!["kwargs"]!["location"]!.GetValue<string>());
    }

    [Fact]
    public void NativeTools_observation_uses_the_tool_role()
    {
        Assert.Equal(("tool", "37.23"), new NativeTools().Observation(37.23));
    }

    [Fact]
    public void NativeTools_is_done_when_there_is_no_tool_call()
    {
        var tools = new NativeTools();

        Assert.True(tools.IsDone(new Response { Content = "Hi" }));
        Assert.False(tools.IsDone(Call("multiply", new JsonObject())));
    }

    // ---- Skills ----

    private static TempFolder CreateSkill()
    {
        var folder = new TempFolder();
        File.WriteAllText(Path.Combine(folder.Path, "SKILL.md"), """
            ---
            name: file_analyzer
            description: Analyze files and provide structured summaries
            ---

            # File Analyzer Skill

            Read the file, then summarize it.
            """);
        File.WriteAllText(Path.Combine(folder.Path, "template.md"), "**Summary**:");
        return folder;
    }

    [Fact]
    public void ParseFrontmatter_reads_key_value_lines()
    {
        var values = Skills.ParseFrontmatter("\nname: file_analyzer\ndescription: Analyze files: carefully\n");

        Assert.Equal("file_analyzer", values["name"]);
        Assert.Equal("Analyze files: carefully", values["description"]);
    }

    [Fact]
    public void AddSkill_registers_only_the_name_and_description()
    {
        using var folder = CreateSkill();
        var skills = new Skills();

        skills.AddSkill(folder.Path);

        var entry = skills.Registry["file_analyzer"];
        Assert.Equal("A skill. Analyze files and provide structured summaries", entry.Description);
        var schema = skills.Schemas![0]!["function"]!;
        Assert.Empty(schema["parameters"]!["properties"]!.AsObject());
    }

    [Fact]
    public async Task Activating_a_skill_returns_its_instructions_and_files()
    {
        using var folder = CreateSkill();
        var skills = new Skills();
        skills.AddSkill(folder.Path);

        var result = Assert.IsType<string>(await skills.ExecuteAsync(Call("file_analyzer", new JsonObject())));

        Assert.StartsWith("# File Analyzer Skill", result);
        Assert.Contains("Read the file, then summarize it.", result);
        Assert.Contains("template.md", result);
        Assert.DoesNotContain("SKILL.md", result.Split("Available files:")[1]);
    }

    // ---- MCP ----

    [Description("Read the content of a markdown file.")]
    private static string ReadMarkdown(string path) => $"# Contents of {path}";

    /// <summary>A real McpServer and McpClient, connected by in-memory pipes instead of a child process.</summary>
    private static async Task<(McpClient Client, Task Server)> ConnectAsync()
    {
        var server = new McpServer("file_reader");
        server.AddTool("read_markdown", ReadMarkdown);

        var toServer = new AnonymousPipeServerStream(PipeDirection.Out);
        var serverInput = new AnonymousPipeClientStream(PipeDirection.In, toServer.ClientSafePipeHandle);
        var fromServer = new AnonymousPipeServerStream(PipeDirection.In);
        var serverOutput = new AnonymousPipeClientStream(PipeDirection.Out, fromServer.ClientSafePipeHandle);

        var serverTask = Task.Run(() => server.RunAsync(new StreamReader(serverInput), new StreamWriter(serverOutput)));
        var client = new McpClient(new StreamReader(fromServer), new StreamWriter(toServer));
        await client.InitializeAsync();
        return (client, serverTask);
    }

    [Fact]
    public async Task McpClient_handshake_learns_the_server_name()
    {
        var (client, _) = await ConnectAsync();
        await using (client)
        {
            Assert.Equal("file_reader", client.ServerInfo!["name"]!.GetValue<string>());
        }
    }

    [Fact]
    public async Task McpClient_lists_the_servers_tools()
    {
        var (client, _) = await ConnectAsync();
        await using (client)
        {
            var tool = Assert.Single(await client.ListToolsAsync());

            Assert.Equal("read_markdown", tool.Name);
            Assert.Equal("Read the content of a markdown file.", tool.Description);
            Assert.Equal("string", tool.InputSchema!["properties"]!["path"]!["type"]!.GetValue<string>());
        }
    }

    [Fact]
    public async Task McpClient_calls_a_tool_and_returns_its_text()
    {
        var (client, _) = await ConnectAsync();
        await using (client)
        {
            var text = await client.CallToolAsync("read_markdown", new JsonObject { ["path"] = "README.md" });

            Assert.Equal("# Contents of README.md", text);
        }
    }

    [Fact]
    public async Task McpTools_turns_server_tools_into_agent_tools()
    {
        var (client, _) = await ConnectAsync();
        await using var tools = await McpTools.ConnectAsync(client);

        Assert.Equal("Read the content of a markdown file.", tools.Registry["read_markdown"].Description);
        var result = await tools.ExecuteAsync(Call("read_markdown", new JsonObject { ["path"] = "notes.md" }));
        Assert.Equal("# Contents of notes.md", result);
    }

    // ---- The chapter 5 agent ----

    [Fact]
    public async Task Agent_adds_the_system_prompt_once()
    {
        var llm = new FakeLlm("Hi!", "Hello again!");
        var agent = new TinyAgent(llm, new Memory(), MathTools());

        await agent.RunAsync("Hi");
        await agent.RunAsync("Hi again");

        var messages = agent.Memory.GetMessages();
        Assert.Single(messages, m => m.Role == "system");
        Assert.StartsWith("You are a helpful assistant.\n\n", messages[0].Content);
        Assert.Contains("`multiply`", messages[0].Content);
    }

    [Fact]
    public async Task Agent_answers_directly_when_no_tool_is_needed()
    {
        var agent = new TinyAgent(new FakeLlm("Flamingos are pink."), new Memory(), MathTools());

        Assert.Equal("Flamingos are pink.", await agent.RunAsync("Tell me about flamingos."));
        Assert.Equal("Flamingos are pink.", agent.Trajectory.LastRun!.Steps[0].Answer);
    }

    [Fact]
    public async Task Agent_runs_a_text_tool_call_and_returns_the_observation()
    {
        var llm = new FakeLlm("""{"tool": "multiply", "kwargs": {"a": "5.1", "b": "7.3"}}""");
        var agent = new TinyAgent(llm, new Memory(), MathTools());

        var result = await agent.RunAsync("What is 5.1 times 7.3?");

        Assert.Equal("OBSERVATION: 37.23", result);
        var last = agent.Memory.GetMessages()[^1];
        Assert.Equal(new ChatMessage("user", "OBSERVATION: 37.23"), last);
        var step = Assert.Single(agent.Trajectory.LastRun!.Steps);
        Assert.Equal("multiply", step.Action!["tool"]!.GetValue<string>());
    }

    [Fact]
    public async Task Agent_with_native_tools_sends_schemas_and_stores_the_raw_tool_call()
    {
        var tools = new NativeTools();
        tools.AddTool("multiply", Toolbox.Multiply);
        var llm = new FakeLlm().ThenToolCall("multiply", """{"a": "5.1", "b": "7.3"}""");
        var agent = new TinyAgent(llm, new Memory(), tools);

        var result = await agent.RunAsync("What is 5.1 times 7.3?");

        Assert.Equal("37.23", result);
        Assert.Single(llm.ToolsSent[0]!);
        var assistant = agent.Memory.GetMessages().Single(m => m.Role == "assistant");
        Assert.Equal("call_1", assistant.ToolCall!["id"]!.GetValue<string>());
        Assert.Equal("tool", agent.Memory.GetMessages()[^1].Role);
    }
}
