namespace IllustratedAgents.Chapters.Ch06;

/// <summary>
/// The autonomous TinyAgent: it loops THOUGHT, ACTION, OBSERVATION until it has an answer or runs out of
/// steps. Chapter 6.
/// </summary>
public class TinyAgent : IAgent
{
    public const string MaxStepsMessage = "Max steps reached without completion.";

    private bool _systemPromptAdded;

    public TinyAgent(ILlm llm, Memory memory, Tools tools, ReAct planner)
    {
        Llm = llm;
        Memory = memory;
        Tools = tools;
        Planner = planner;
    }

    protected ILlm Llm { get; }
    public Memory Memory { get; }
    public Tools Tools { get; }
    public ReAct Planner { get; }
    public Trajectory Trajectory { get; } = new();

    /// <summary>"You are a helpful assistant." followed by the planner's prompt, then the tools' prompt.</summary>
    public string SystemPrompt
    {
        get
        {
            return "You are a helpful assistant.\n\n" + Planner.Prompt + Tools.Prompt;
        }
    }

    public Task<string> RunAsync(string task, CancellationToken cancellationToken = default) =>
        RunAsync(task, imageData: null, cancellationToken);

    /// <summary>
    /// Add the system prompt on the first run, add the task, start a run, then step until a step returns an
    /// answer. After <see cref="ReAct.MaxSteps"/> steps without one, return <see cref="MaxStepsMessage"/>.
    /// </summary>
    protected async Task<string> RunAsync(string task, string? imageData, CancellationToken cancellationToken)
    {
        if (!_systemPromptAdded)
        {
            await Memory.AddAsync("system", SystemPrompt, cancellationToken: cancellationToken);
            _systemPromptAdded = true;
        }

        await Memory.AddAsync("user", task, imageData: imageData, cancellationToken: cancellationToken);
        Trajectory.Initialize(task);

        // The autonomy loop
        for (var step = 0; step < Planner.MaxSteps; step++)
        {
            var result = await StepAsync(cancellationToken);
            if (result is not null)
            {
                return result;
            }
        }

        return MaxStepsMessage;
    }

    /// <summary>
    /// One step: generate, store the reply, let the planner parse it and then the tools. Return the answer if
    /// done; otherwise run the tool and return null so the loop continues.
    /// </summary>
    protected async Task<string?> StepAsync(CancellationToken cancellationToken)
    {
        // THOUGHT: generate a response and add it to memory
        var response = await Llm.GenerateAsync(Memory.GetMessages(), Tools.Schemas, cancellationToken);
        await Memory.AddAsync("assistant", response.Content, response.ToolCall, cancellationToken: cancellationToken);

        // Parse the plan, then the tool call
        response = Planner.Parse(response);
        response = Tools.Parse(response);

        // ANSWER: the stopping rule
        if (Tools.IsDone(response))
        {
            Trajectory.Add(response);
            return response.Content;
        }

        await ExecuteActionAsync(response, cancellationToken);
        return null;
    }

    /// <summary>ACTION: run the tool. OBSERVATION: store the result in memory and the trajectory.</summary>
    protected async Task ExecuteActionAsync(Response response, CancellationToken cancellationToken)
    {
        var result = await Tools.ExecuteAsync(response, cancellationToken);
        var (role, observation) = Tools.Observation(result);
        await Memory.AddAsync(role, observation, cancellationToken: cancellationToken);
        Trajectory.Add(response, observation);
    }
}
