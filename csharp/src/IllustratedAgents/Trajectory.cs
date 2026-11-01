using System.Text.Json.Nodes;

namespace IllustratedAgents;

/// <summary>One step of an agent's work: a THOUGHT, then either an ACTION with its OBSERVATION, or an ANSWER.</summary>
public sealed class Step
{
    public string Thought { get; set; } = "";
    public JsonObject? Action { get; set; }
    public string? Observation { get; set; }
    public string? Answer { get; set; }
    public ResponseMetadata? Metadata { get; set; }
}

/// <summary>One call to the agent: the task it was given and every step it took.</summary>
public sealed class Run
{
    public Run(string query) => Query = query;

    public string Query { get; }
    public List<Step> Steps { get; } = [];
}

/// <summary>Records everything an agent did, run by run. Chapter 2.</summary>
public sealed class Trajectory
{
    public List<Run> Runs { get; } = [];

    /// <summary>All steps across all runs, in order.</summary>
    public IEnumerable<Step> Steps => Runs.SelectMany(run => run.Steps);

    /// <summary>The most recent run, or null before the first one.</summary>
    public Run? LastRun => Runs.Count > 0 ? Runs[^1] : null;

    /// <summary>Start a new run for <paramref name="query"/>.</summary>
    public void Initialize(string query)
    {
        Runs.Add(new Run(query));
    }

    /// <summary>
    /// Record a step from <paramref name="response"/>. With an <paramref name="observation"/> the step is an
    /// ACTION; without one it is the final ANSWER.
    /// </summary>
    public void Add(Response response, string? observation = null)
    {
        // THOUGHT
        var step = new Step
        {
            Thought = response.Reasoning ?? "",
            Metadata = response.Metadata,
        };

        // ACTION and OBSERVATION, or ANSWER
        if (observation is not null)
        {
            step.Action = response.ToolCall?.DeepClone().AsObject();
            step.Observation = observation;
        }
        else
        {
            step.Answer = response.Content;
        }

        Runs[^1].Steps.Add(step);
    }
}
