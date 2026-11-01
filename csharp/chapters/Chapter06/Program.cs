// Chapter 6: planning and autonomy. Run with an argument to choose the demo:
//   dotnet run           ReAct with text parsing (gemma3:12b)
//   dotnet run native    ReAct with native reasoning and tool calling (gemma4:e4b)
//   dotnet run plan      Plan-and-Solve: the model keeps its own checklist (gemma4:e4b)
//   dotnet run skills    the chapter 5 skill, now finished by the autonomous loop (gemma4:e4b)
using IllustratedAgents;
using TinyAgent = IllustratedAgents.Chapters.Ch06.TinyAgent;

const string task = "What is (4.6 + 6.685) x 4, and then subtract 3.14 from the result?";

static Tools Arithmetic(Tools tools)
{
    tools.AddTool("add", Toolbox.Add, "add(a: str, b: str)");
    tools.AddTool("subtract", Toolbox.Subtract, "subtract(a: str, b: str)");
    tools.AddTool("multiply", Toolbox.Multiply, "multiply(a: str, b: str)");
    return tools;
}

switch (args.FirstOrDefault() ?? "react")
{
    case "react":
    {
        var agent = new TinyAgent(Llm.FromEnvironment("gemma3:12b"), new Memory(), Arithmetic(new Tools()), new ReAct(maxSteps: 10));
        Console.WriteLine(await agent.RunAsync(task) + "\n");
        TrajectoryView.Print(agent.Trajectory);
        break;
    }

    case "native":
    {
        var agent = new TinyAgent(Llm.FromEnvironment("gemma4:e4b", think: true), new Memory(), Arithmetic(new NativeTools()), new NativeReAct(maxSteps: 10));
        Console.WriteLine(await agent.RunAsync(task) + "\n");
        TrajectoryView.Print(agent.Trajectory);
        break;
    }

    case "plan":
    {
        var tools = Arithmetic(new NativeTools());
        var planner = new PlanAndSolve(tools, maxSteps: 15);
        var agent = new TinyAgent(Llm.FromEnvironment("gemma4:e4b", think: true), new Memory(), tools, planner);
        Console.WriteLine(await agent.RunAsync(task) + "\n");
        Console.WriteLine("Final plan:\n" + planner.Render() + "\n");
        TrajectoryView.Print(agent.Trajectory);
        break;
    }

    case "skills":
    {
        var tools = new Skills();
        tools.AddSkill(Path.Combine(AppContext.BaseDirectory, "skills", "file_analyzer"));
        tools.AddTool("read_markdown", Toolbox.ReadMarkdown);
        var agent = new TinyAgent(Llm.FromEnvironment("gemma4:e4b", think: true), new Memory(), tools, new NativeReAct());
        Console.WriteLine(await agent.RunAsync(
            "Use the `file_analyzer` skill to summarize https://raw.githubusercontent.com/HandsOnLLM/Hands-On-Large-Language-Models/refs/heads/main/README.md."));
        break;
    }

    default:
        Console.WriteLine("Choose one: react, native, plan, skills");
        break;
}
