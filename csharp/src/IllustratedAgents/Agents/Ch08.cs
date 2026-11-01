namespace IllustratedAgents.Chapters.Ch08;

/// <summary>
/// Multi-agent collaboration with agents as tools: two specialists, and an orchestrator whose only tools
/// are "ask the math agent" and "ask the date agent". Chapter 8.
/// </summary>
public static class Team
{
    /// <summary>A native-tool agent with <c>add</c>, <c>subtract</c> and <c>multiply</c>.</summary>
    public static Ch06.TinyAgent CreateMathAgent(ILlm llm)
    {
        var tools = new NativeTools();
        tools.AddTool("add", Toolbox.Add, "Add two numbers.");
        tools.AddTool("subtract", Toolbox.Subtract, "Subtract two numbers.");
        tools.AddTool("multiply", Toolbox.Multiply, "Multiply two numbers.");
        return new Ch06.TinyAgent(llm, new Memory(), tools, new NativeReAct());
    }

    /// <summary>A native-tool agent with <c>today</c> and <c>days_between</c>.</summary>
    public static Ch06.TinyAgent CreateDateAgent(ILlm llm)
    {
        var tools = new NativeTools();
        tools.AddTool("today", Toolbox.Today, "Return today's date (YYYY-MM-DD).");
        tools.AddTool("days_between", Toolbox.DaysBetween, "Days between two ISO dates.");
        return new Ch06.TinyAgent(llm, new Memory(), tools, new NativeReAct());
    }

    /// <summary>
    /// An orchestrator with two tools, <c>ask_math_agent(question)</c> and <c>ask_date_agent(question)</c>,
    /// each of which runs the specialist on the question and returns its answer.
    /// </summary>
    public static Ch06.TinyAgent CreateOrchestrator(ILlm llm, IAgent mathAgent, IAgent dateAgent)
    {
        Func<string, CancellationToken, Task<string>> askMathAgent = (question, token) => mathAgent.RunAsync(question, token);
        Func<string, CancellationToken, Task<string>> askDateAgent = (question, token) => dateAgent.RunAsync(question, token);

        var tools = new NativeTools();
        tools.AddTool("ask_math_agent", askMathAgent, "Delegate to the math specialist.");
        tools.AddTool("ask_date_agent", askDateAgent, "Ask queries to a sub-Agent that handles ISO dates.");
        return new Ch06.TinyAgent(llm, new Memory(), tools, new NativeReAct());
    }
}
