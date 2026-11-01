// Chapter 5: tools. Run with an argument to choose the demo:
//   dotnet run           text-based tool calling (gemma3:12b)
//   dotnet run mcp       tools from an MCP server, started as a child process (gemma3:12b)
//   dotnet run native    native function calling (gemma4:e4b)
//   dotnet run skills    a SKILL.md skill plus a tool (gemma4:e4b)
// Set TINYAGENT_MODEL to override the model for every demo.
using IllustratedAgents;
using TinyAgent = IllustratedAgents.Chapters.Ch05.TinyAgent;

const string readme = "https://raw.githubusercontent.com/HandsOnLLM/Hands-On-Large-Language-Models/refs/heads/main/README.md";

switch (args.FirstOrDefault() ?? "tools")
{
    case "tools":
    {
        var tools = new Tools();
        tools.AddTool("multiply", Toolbox.Multiply, "Multiplies two numbers: multiply(a: str, b: str)");
        tools.AddTool("get_weather", Toolbox.GetWeather, "Gets weather: get_weather(location: str)");
        Console.WriteLine(tools.Prompt);

        var agent = new TinyAgent(Llm.FromEnvironment("gemma3:12b"), new Memory(), tools);
        Console.WriteLine(await agent.RunAsync("What is 5.1 times 7.3?"));
        Console.WriteLine(await agent.RunAsync("Hi! Tell me something about flamingos in two sentences."));
        Console.WriteLine();
        TrajectoryView.Print(agent.Trajectory);
        TrajectoryView.PrintMessages(agent.Memory.GetMessages());
        break;
    }

    case "mcp":
    {
        // The server project is built next to this app; start it with the same dotnet that runs us
        var serverDll = Path.Combine(AppContext.BaseDirectory, "Chapter05.McpServer.dll");
        await using var tools = await McpTools.StartAsync("dotnet", [serverDll]);
        Console.WriteLine("Tools from the MCP server:");
        Console.WriteLine(tools.Descriptions + "\n");

        var agent = new TinyAgent(Llm.FromEnvironment("gemma3:12b"), new Memory(), tools);
        Console.WriteLine(await agent.RunAsync($"Read the file at '{readme}'"));
        break;
    }

    case "native":
    {
        // The schema the model receives for one tool
        Console.WriteLine(ToolSchema.FromDelegate("multiply", Toolbox.Multiply).ToJsonString(new() { WriteIndented = true }));

        var tools = new NativeTools();
        tools.AddTool("multiply", Toolbox.Multiply);
        tools.AddTool("get_weather", Toolbox.GetWeather);

        var agent = new TinyAgent(Llm.FromEnvironment("gemma4:e4b"), new Memory(), tools);
        Console.WriteLine(await agent.RunAsync("What is 5.1 times 7.3?"));
        Console.WriteLine(await agent.RunAsync("Hi! Tell me something about flamingos in two sentences."));
        Console.WriteLine();
        TrajectoryView.Print(agent.Trajectory);
        break;
    }

    case "skills":
    {
        var skillFolder = Path.Combine(AppContext.BaseDirectory, "skills", "file_analyzer");
        var tools = new Skills();
        tools.AddSkill(skillFolder);
        tools.AddTool("read_markdown", Toolbox.ReadMarkdown);
        Console.WriteLine($"Catalog entry: {tools.Registry["file_analyzer"].Description}\n");

        var agent = new TinyAgent(Llm.FromEnvironment("gemma4:e4b"), new Memory(), tools);
        // The chapter 5 agent takes one step, so this shows the skill activating; chapter 6 finishes the job.
        Console.WriteLine(await agent.RunAsync($"Use the `file_analyzer` skill to summarize {readme}."));
        break;
    }

    default:
        Console.WriteLine("Choose one: tools, mcp, native, skills");
        break;
}
