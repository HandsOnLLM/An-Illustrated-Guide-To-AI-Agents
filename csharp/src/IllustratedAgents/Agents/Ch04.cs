namespace IllustratedAgents.Chapters.Ch04;

/// <summary>TinyAgent with memory: each run sees the whole conversation so far. Chapter 4.</summary>
public sealed class TinyAgent : IAgent
{
    private readonly ILlm _llm;

    public TinyAgent(ILlm llm, Memory memory)
    {
        _llm = llm;
        Memory = memory;
    }

    public Memory Memory { get; }

    public Trajectory Trajectory { get; } = new();

    /// <summary>Add the task to memory, start a run, take one step.</summary>
    public async Task<string> RunAsync(string task, CancellationToken cancellationToken = default)
    {
        await Memory.AddAsync("user", task, cancellationToken: cancellationToken);
        Trajectory.Initialize(task);
        return await StepAsync(cancellationToken);
    }

    /// <summary>Generate from everything in memory, store the reply in memory and the trajectory, return it.</summary>
    private async Task<string> StepAsync(CancellationToken cancellationToken)
    {
        var response = await _llm.GenerateAsync(Memory.GetMessages(), cancellationToken: cancellationToken);
        await Memory.AddAsync("assistant", response.Content, cancellationToken: cancellationToken);
        Trajectory.Add(response);
        return response.Content;
    }
}
