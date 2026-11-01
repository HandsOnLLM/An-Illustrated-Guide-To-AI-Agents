namespace IllustratedAgents.Chapters.Ch09;

/// <summary>The chapter 6 agent, now able to take an image with a task. Chapter 9.</summary>
public sealed class TinyAgent : Ch06.TinyAgent
{
    public TinyAgent(ILlm llm, Memory memory, Tools tools, ReAct planner)
        : base(llm, memory, tools, planner)
    {
    }

    /// <summary>
    /// Run the agent on a task with an image: a web address or base64 data. Use a
    /// <see cref="MultimodalMemory"/>; plain memory ignores the image.
    /// </summary>
    public new Task<string> RunAsync(string task, string? imageData, CancellationToken cancellationToken = default)
    {
        return base.RunAsync(task, imageData, cancellationToken);
    }
}
