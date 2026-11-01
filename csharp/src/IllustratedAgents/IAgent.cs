namespace IllustratedAgents;

/// <summary>
/// Anything you can hand a task to. Every TinyAgent from chapter 2 onward implements it, which is what
/// lets chapter 7 evaluate any agent and chapter 8 use one agent as another agent's tool.
/// </summary>
public interface IAgent
{
    Task<string> RunAsync(string task, CancellationToken cancellationToken = default);

    Trajectory Trajectory { get; }
}
