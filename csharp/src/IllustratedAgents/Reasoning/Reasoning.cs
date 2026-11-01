using System.Text.RegularExpressions;

namespace IllustratedAgents;

/// <summary>
/// The answer-improving techniques from chapter 3: self-consistency (ask several times, take the most
/// common answer) and best-of-N (ask several times, keep the answer a verifier scores highest).
/// </summary>
public static class Reasoning
{
    /// <summary>
    /// The text after the last <paramref name="marker"/>, with line breaks removed and trimmed.
    /// Text without the marker is returned whole, trimmed.
    /// </summary>
    public static string ExtractAnswer(string text, string marker = "Answer:")
    {
        var lastMarker = text.LastIndexOf(marker, StringComparison.Ordinal);
        var answer = lastMarker >= 0 ? text[(lastMarker + marker.Length)..] : text;
        return answer.Replace("\n", "").Replace("\r", "").Trim();
    }

    /// <summary>How many times each answer appears, most common first.</summary>
    public static IReadOnlyList<KeyValuePair<string, int>> CountVotes(IEnumerable<string> answers)
    {
        return answers
            .GroupBy(answer => answer)
            .Select(group => KeyValuePair.Create(group.Key, group.Count()))
            .OrderByDescending(pair => pair.Value)
            .ToList();
    }

    /// <summary>
    /// Self-consistency: ask the same question <paramref name="samples"/> times (use a temperature above 0 so
    /// the answers vary), extract each answer, and return the most common one with the full vote count.
    /// </summary>
    public static async Task<(string Answer, IReadOnlyList<KeyValuePair<string, int>> Votes)> SelfConsistencyAsync(
        ILlm llm,
        string query,
        int samples = 10,
        CancellationToken cancellationToken = default)
    {
        var answers = new List<string>();
        for (var i = 0; i < samples; i++)
        {
            var response = await llm.GenerateAsync([new ChatMessage("user", query)], cancellationToken: cancellationToken);
            answers.Add(ExtractAnswer(response.Content));
        }

        var votes = CountVotes(answers);
        return (votes.Count > 0 ? votes[0].Key : "", votes);
    }

    /// <summary>
    /// Best-of-N: generate <paramref name="n"/> candidate answers, score each with <paramref name="verify"/>
    /// (0 to 1), and return the best one with its score and every score in order.
    /// </summary>
    public static async Task<(string Best, double Score, IReadOnlyList<double> Scores)> BestOfNAsync(
        ILlm llm,
        string prompt,
        Func<string, double> verify,
        int n = 10,
        CancellationToken cancellationToken = default)
    {
        var candidates = new List<(string Answer, double Score)>();
        for (var i = 0; i < n; i++)
        {
            var response = await llm.GenerateAsync([new ChatMessage("user", prompt)], cancellationToken: cancellationToken);
            candidates.Add((response.Content, verify(response.Content)));
        }

        if (candidates.Count == 0)
        {
            return ("", 0, []);
        }

        var best = candidates.MaxBy(candidate => candidate.Score);
        return (best.Answer, best.Score, candidates.Select(candidate => candidate.Score).ToList());
    }

    /// <summary>
    /// The verifier for chapter 3's best-of-N demo. The Python version runs generated Python code; here the
    /// model writes a regular expression for valid Roman numerals (1 to 3999), and the score is the share of
    /// test strings it classifies correctly. A pattern that doesn't compile scores 0.
    /// </summary>
    public static double ScoreRomanNumeralRegex(string candidate)
    {
        string[] valid = ["III", "IV", "IX", "LVIII", "MCMXCIV", "MMMCMXCIX"];
        string[] invalid = ["", "IIII", "VV", "IC", "ABC", "MMMM"];

        Regex regex;
        try
        {
            regex = new Regex($"^(?:{CleanPattern(candidate)})$", RegexOptions.None, TimeSpan.FromSeconds(1));
        }
        catch (ArgumentException)
        {
            return 0;
        }

        try
        {
            var correct = valid.Count(regex.IsMatch) + invalid.Count(text => !regex.IsMatch(text));
            return (double)correct / (valid.Length + invalid.Length);
        }
        catch (RegexMatchTimeoutException)
        {
            return 0;
        }
    }

    /// <summary>Strips the code fences, slashes and anchors a model tends to wrap a regex in. Provided for you.</summary>
    public static string CleanPattern(string candidate)
    {
        var pattern = candidate.Trim();
        pattern = Regex.Replace(pattern, @"^```[a-zA-Z]*\s*|\s*```$", "").Trim();
        if (pattern.Length > 1 && pattern.StartsWith('/') && pattern.EndsWith('/'))
        {
            pattern = pattern[1..^1];
        }
        if (pattern.StartsWith('^'))
        {
            pattern = pattern[1..];
        }
        if (pattern.EndsWith('$') && !pattern.EndsWith(@"\$"))
        {
            pattern = pattern[..^1];
        }
        return pattern;
    }
}
