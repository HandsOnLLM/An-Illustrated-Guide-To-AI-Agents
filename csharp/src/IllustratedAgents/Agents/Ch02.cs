namespace IllustratedAgents.Chapters.Ch02;

/// <summary>TinyAgent with a brain: one call to the model per task, recorded in a trajectory. Chapter 2.</summary>
public sealed class TinyAgent : IAgent
{
    private readonly ILlm _llm;

    public TinyAgent(ILlm llm) => _llm = llm;

    public Trajectory Trajectory { get; } = new();

    /// <summary>Start a run in the trajectory, take one step, and return the model's answer.</summary>
    public async Task<string> RunAsync(string task, CancellationToken cancellationToken = default)
    {
        Trajectory.Initialize(task);
        return await StepAsync(task, cancellationToken);
    }

    /// <summary>Send the task as a single user message, record the response, return its content.</summary>
    private async Task<string> StepAsync(string task, CancellationToken cancellationToken)
    {
        var response = await _llm.GenerateAsync([new ChatMessage("user", task)], cancellationToken: cancellationToken);
        Trajectory.Add(response);
        return response.Content;
    }
}
