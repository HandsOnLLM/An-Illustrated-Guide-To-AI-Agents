namespace IllustratedAgents.Chapters.Ch05;

/// <summary>
/// TinyAgent with tools: in one step the model either answers or calls a tool. Not autonomous yet: after a
/// tool runs, the run ends with the observation. Chapter 5.
/// </summary>
public sealed class TinyAgent : IAgent
{
    private readonly ILlm _llm;
    private bool _systemPromptAdded;

    public TinyAgent(ILlm llm, Memory memory, Tools tools)
    {
        _llm = llm;
        Memory = memory;
        Tools = tools;
    }

    public Memory Memory { get; }
    public Tools Tools { get; }
    public Trajectory Trajectory { get; } = new();

    /// <summary>"You are a helpful assistant." followed by the tools' prompt.</summary>
    public string SystemPrompt
    {
        get
        {
            return "You are a helpful assistant.\n\n" + Tools.Prompt;
        }
    }

    /// <summary>
    /// On the first run, add the system prompt to memory (a constructor can't await). Then add the task,
    /// start a run, and take one step.
    /// </summary>
    public async Task<string> RunAsync(string task, CancellationToken cancellationToken = default)
    {
        if (!_systemPromptAdded)
        {
            await Memory.AddAsync("system", SystemPrompt, cancellationToken: cancellationToken);
            _systemPromptAdded = true;
        }

        await Memory.AddAsync("user", task, cancellationToken: cancellationToken);
        Trajectory.Initialize(task);
        return await StepAsync(cancellationToken);
    }

    /// <summary>
    /// THOUGHT: generate with the tool schemas, store the reply (and any tool call) in memory. Parse the tool
    /// call. ANSWER: if done, record and return the content. Otherwise run the tool and return the observation.
    /// </summary>
    private async Task<string> StepAsync(CancellationToken cancellationToken)
    {
        var response = await _llm.GenerateAsync(Memory.GetMessages(), Tools.Schemas, cancellationToken);
        await Memory.AddAsync("assistant", response.Content, response.ToolCall, cancellationToken: cancellationToken);

        response = Tools.Parse(response);

        if (Tools.IsDone(response))
        {
            Trajectory.Add(response);
            return response.Content;
        }

        return await ExecuteActionAsync(response, cancellationToken);
    }

    /// <summary>ACTION: run the tool. OBSERVATION: store the result in memory and the trajectory, and return it.</summary>
    private async Task<string> ExecuteActionAsync(Response response, CancellationToken cancellationToken)
    {
        var result = await Tools.ExecuteAsync(response, cancellationToken);
        var (role, observation) = Tools.Observation(result);
        await Memory.AddAsync(role, observation, cancellationToken: cancellationToken);
        Trajectory.Add(response, observation);
        return observation;
    }
}
