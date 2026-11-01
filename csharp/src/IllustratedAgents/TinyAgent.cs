namespace IllustratedAgents;

/// <summary>
/// The finished TinyAgent: model, memory, tools, planning, images, and a display that shows each THOUGHT,
/// ACTION, OBSERVATION and ANSWER as it happens. Chapter 10.
/// </summary>
public sealed class TinyAgent : IAgent
{
    public const string MaxStepsMessage = "Max steps reached without completion.";

    private readonly ILlm _llm;
    private bool _systemPromptAdded;

    public TinyAgent(ILlm llm, Memory memory, Tools tools, ReAct planner, Display? display = null)
    {
        _llm = llm;
        Memory = memory;
        Tools = tools;
        Planner = planner;
        Display = display ?? new Display();
    }

    public Memory Memory { get; }
    public Tools Tools { get; }
    public ReAct Planner { get; }
    public Display Display { get; }
    public Trajectory Trajectory { get; } = new();

    public string SystemPrompt => "You are a helpful assistant.\n\n" + Planner.Prompt + Tools.Prompt;

    public Task<string> RunAsync(string task, CancellationToken cancellationToken = default) =>
        RunAsync(task, imageData: null, cancellationToken);

    /// <summary>The chapter 6 loop, with an optional image (chapter 9).</summary>
    public async Task<string> RunAsync(string task, string? imageData, CancellationToken cancellationToken = default)
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
    /// The chapter 6 step, telling the display what's happening: <see cref="Display.Thinking"/> before the model
    /// call, <see cref="Display.ShowResponse"/> after it.
    /// </summary>
    private async Task<string?> StepAsync(CancellationToken cancellationToken)
    {
        // THOUGHT: generate a response and add it to memory
        Display.Thinking();
        var response = await _llm.GenerateAsync(Memory.GetMessages(), Tools.Schemas, cancellationToken);
        await Memory.AddAsync("assistant", response.Content, response.ToolCall, cancellationToken: cancellationToken);
        Display.ShowResponse(response);

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

    /// <summary>
    /// The chapter 6 action, telling the display what's happening: <see cref="Display.ShowToolCall"/> before
    /// the tool runs, <see cref="Display.ShowObservation"/> after.
    /// </summary>
    private async Task ExecuteActionAsync(Response response, CancellationToken cancellationToken)
    {
        // ACTION: run the tool
        Display.ShowToolCall(response);
        var result = await Tools.ExecuteAsync(response, cancellationToken);

        // OBSERVATION: store the result and show it
        var (role, observation) = Tools.Observation(result);
        await Memory.AddAsync(role, observation, cancellationToken: cancellationToken);
        Trajectory.Add(response, observation);
        Display.ShowObservation(observation);
    }
}
