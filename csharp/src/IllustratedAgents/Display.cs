using System.Text.Encodings.Web;
using System.Text.Json;

namespace IllustratedAgents;

/// <summary>
/// Where the agent reports what it's doing. This base class shows nothing, which is what tests and
/// evaluations want. <see cref="ConsoleDisplay"/> prints each event in colour. Chapter 10.
/// </summary>
public class Display
{
    public virtual void Thinking() { }

    public virtual void ShowResponse(Response response) { }

    public virtual void ShowToolCall(Response response) { }

    public virtual void ShowObservation(string observation) { }
}

/// <summary>
/// Prints a trajectory or a conversation after the fact: the console version of the book's
/// <c>TrajectoryViewer</c>. Provided for you.
/// </summary>
public static class TrajectoryView
{
    /// <summary>Shows JSON the way a person wrote it: no escaping of quotes, angle brackets or accented letters.</summary>
    internal static readonly JsonSerializerOptions Readable = new() { Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping };

    public static void Print(Trajectory trajectory)
    {
        foreach (var run in trajectory.Runs)
        {
            Console.WriteLine($"── Run: {run.Query}");
            for (var i = 0; i < run.Steps.Count; i++)
            {
                var step = run.Steps[i];
                Console.WriteLine($"   Step {i + 1}");
                if (!string.IsNullOrWhiteSpace(step.Thought)) Console.WriteLine($"     THOUGHT:     {step.Thought}");
                if (step.Action is not null) Console.WriteLine($"     ACTION:      {step.Action.ToJsonString(Readable)}");
                if (step.Observation is not null) Console.WriteLine($"     OBSERVATION: {step.Observation}");
                if (step.Answer is not null) Console.WriteLine($"     ANSWER:      {step.Answer}");
                if (step.Metadata is not null) Console.WriteLine($"     ({step.Metadata.Model}: {step.Metadata.PromptTokens} prompt + {step.Metadata.CompletionTokens} completion tokens)");
            }
        }
        Console.WriteLine();
    }

    public static void PrintMessages(IEnumerable<ChatMessage> messages)
    {
        foreach (var message in messages)
        {
            var content = message.Parts is { Count: > 0 } parts
                ? string.Join(" + ", parts.Select(p => p.Type == "text" ? p.Text : $"[image {Shorten(p.ImageUrl ?? "", 60)}]"))
                : message.Content;
            var toolCall = message.ToolCall is null ? "" : $"  [tool call: {message.ToolCall.ToJsonString(Readable)}]";
            Console.WriteLine($"[{message.Role}] {Shorten(content ?? "", 400)}{toolCall}");
        }
        Console.WriteLine();
    }

    private static string Shorten(string text, int max) =>
        text.Length <= max ? text : text[..max] + "…";
}

/// <summary>
/// Prints THOUGHT in green, ACTION in red, OBSERVATION in yellow and ANSWER in purple, like the book's
/// terminal agent. Provided for you: styling, not an agent concept.
/// </summary>
public sealed class ConsoleDisplay : Display
{
    private const string Bold = "\u001b[1m";
    private const string Reset = "\u001b[0m";
    private const string Green = "\u001b[32m";
    private const string Red = "\u001b[31m";
    private const string Yellow = "\u001b[33m";
    private const string Purple = "\u001b[35m";

    public override void Thinking() => Console.WriteLine($"  Thinking...\n{Reset}");

    public override void ShowResponse(Response response)
    {
        if (!string.IsNullOrWhiteSpace(response.Reasoning))
        {
            Console.WriteLine($"{Bold}{Green}{"▒▒ THOUGHT ▒▒",-13}{Reset}");
            Console.WriteLine($"{response.Reasoning}{Reset}\n");
        }

        if (!string.IsNullOrWhiteSpace(response.Content))
        {
            Console.WriteLine($"{Bold}{Purple}{"▒▒ ANSWER ▒▒",-13}{Reset}");
            Console.WriteLine($"{response.Content}{Reset}\n");
        }
    }

    public override void ShowToolCall(Response response)
    {
        var tool = response.ToolCall?["tool"]?.ToString();
        var kwargs = response.ToolCall?["kwargs"]?.ToJsonString(TrajectoryView.Readable);
        Console.WriteLine($"{Bold}{Red}{"▒▒ ACTION ▒▒",-13}{Reset}");
        Console.WriteLine($"{tool}({kwargs}){Reset}\n");
    }

    public override void ShowObservation(string observation)
    {
        Console.WriteLine($"{Bold}{Yellow}{"▒▒ OBSERVATION ▒▒",-13}{Reset}");
        Console.WriteLine($"{observation}{Reset}\n");
        Console.WriteLine($"{new string('─', 40)}STEP{new string('─', 40)}{Reset}\n");
    }
}
