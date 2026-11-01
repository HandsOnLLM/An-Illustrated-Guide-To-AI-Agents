namespace IllustratedAgents.Chapters.Ch01;

/// <summary>
/// The TinyAgent skeleton: no model, no memory, no tools yet. Every later chapter fills in one of these
/// empty slots. Chapter 1.
/// </summary>
public sealed class TinyAgent
{
    public object? Llm { get; } = null;      // Chapters 2 and 3: add a model
    public object? Memory { get; } = null;   // Chapter 4: add memory
    public object? Tools { get; } = null;    // Chapter 5: add tools
    public object? Planner { get; } = null;  // Chapter 6: add planning

    /// <summary>Run the agent on a task: for now, a single step.</summary>
    public string Run(string task)
    {
        return Step(task);
    }

    /// <summary>One step. For now it only echoes the task back as "Received: task".</summary>
    private string Step(string task)
    {
        return $"Received: {task}";
    }

    /// <summary>A placeholder that later chapters replace with real tool calls: "Executed action: action".</summary>
    public string ExecuteAction(string action)
    {
        return $"Executed action: {action}";
    }
}
