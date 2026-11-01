using System.Globalization;
using System.Text.RegularExpressions;

namespace IllustratedAgents;

/// <summary>One benchmark question: the task, and either the expected answer or a check function.</summary>
public sealed record Example(string Task, string? Expected = null, Func<string, bool>? Check = null);

/// <summary>Scores a prediction against an example: 0 is a fail, 1 a pass, anything between is partial credit.</summary>
public delegate Task<double> Scorer(string prediction, Example example);

/// <summary>A named set of examples and the scorer that grades them. Chapter 7.</summary>
public sealed record Benchmark(string Name, IReadOnlyList<Example> Examples, Scorer Scorer);

/// <summary>How the agent did on one example.</summary>
public sealed record ExampleResult(string Prediction, double Score);

/// <summary>How the agent did on a whole benchmark.</summary>
public sealed record EvaluationResult(string Name, double PassRate, IReadOnlyList<ExampleResult> Results);

/// <summary>Runs a fresh agent on every example in a benchmark and averages the scores. Chapter 7.</summary>
public sealed class Evaluator
{
    private readonly Func<IAgent> _createAgent;

    /// <param name="createAgent">Builds a new agent, so no example sees another example's memory.</param>
    public Evaluator(Func<IAgent> createAgent) => _createAgent = createAgent;

    public async Task<EvaluationResult> RunAsync(Benchmark benchmark, CancellationToken cancellationToken = default)
    {
        // Run each example with a fresh agent and score it
        var results = new List<ExampleResult>();
        foreach (var example in benchmark.Examples)
        {
            var agent = _createAgent();
            var prediction = await agent.RunAsync(example.Task, cancellationToken) ?? "";
            var score = await benchmark.Scorer(prediction, example);
            results.Add(new ExampleResult(prediction, score));
        }

        // Aggregate into a pass rate
        var passRate = results.Count > 0 ? results.Average(result => result.Score) : 0.0;
        return new EvaluationResult(benchmark.Name, passRate, results);
    }
}

/// <summary>The three scorers from chapter 7.</summary>
public static class Scorers
{
    /// <summary>
    /// Exact match for multiple choice: the first standalone letter A to J in the prediction must equal
    /// <see cref="Example.Expected"/>. No letter scores 0.
    /// </summary>
    public static Task<double> ExactMatch(string prediction, Example example)
    {
        var match = Regex.Match(prediction.ToUpperInvariant(), @"\b([A-J])\b");
        var passed = match.Success && match.Groups[1].Value == example.Expected;
        return Task.FromResult(passed ? 1.0 : 0.0);
    }

    /// <summary>Programmatic check: the example's own <see cref="Example.Check"/> decides.</summary>
    public static Task<double> Programmatic(string prediction, Example example)
    {
        var passed = example.Check?.Invoke(prediction) ?? false;
        return Task.FromResult(passed ? 1.0 : 0.0);
    }

    /// <summary>
    /// LLM-as-a-judge: <paramref name="judge"/> scores the response against the expected answer from 0.0 to 1.0.
    /// A reply that isn't a number scores 0.
    /// </summary>
    public static Scorer Judge(ILlm judge)
    {
        return async (prediction, example) =>
        {
            var prompt = $"""

                Score the response from 0.0 to 1.0.

                Expected: {example.Expected}
                Response: {prediction}

                Reply with only a single number.

                """;
            var response = await judge.GenerateAsync([new ChatMessage("user", prompt)]);
            var firstWord = response.Content.Trim().Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries).FirstOrDefault() ?? "";
            return double.TryParse(firstWord, NumberStyles.Float, CultureInfo.InvariantCulture, out var score)
                ? Math.Clamp(score, 0.0, 1.0)
                : 0.0;
        };
    }
}
