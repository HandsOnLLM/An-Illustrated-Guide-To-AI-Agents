namespace IllustratedAgents.Tests;

public class Chapter03Tests
{
    [Fact]
    public void ExtractAnswer_takes_the_text_after_the_last_marker()
    {
        var text = "Answer: maybe 2\nLet me check again.\nAnswer:\n 4 \n";

        Assert.Equal("4", Reasoning.ExtractAnswer(text));
    }

    [Fact]
    public void ExtractAnswer_without_a_marker_returns_the_trimmed_text()
    {
        Assert.Equal("seat 4", Reasoning.ExtractAnswer("  seat 4\n"));
    }

    [Fact]
    public void CountVotes_puts_the_most_common_answer_first()
    {
        var votes = Reasoning.CountVotes(["4", "5", "4", "3", "4", "5"]);

        Assert.Equal("4", votes[0].Key);
        Assert.Equal(3, votes[0].Value);
        Assert.Equal("5", votes[1].Key);
        Assert.Equal(2, votes[1].Value);
    }

    [Fact]
    public async Task SelfConsistency_returns_the_majority_answer()
    {
        var llm = new FakeLlm("... Answer: 4", "... Answer: 5", "... Answer: 4", "... Answer: 4", "... Answer: 2");

        var (answer, votes) = await Reasoning.SelfConsistencyAsync(llm, "In which seat is Maarten sitting?", samples: 5);

        Assert.Equal("4", answer);
        Assert.Equal(3, votes.First(v => v.Key == "4").Value);
        Assert.Equal(5, llm.Calls.Count);
    }

    [Fact]
    public async Task BestOfN_keeps_the_highest_scoring_candidate()
    {
        var llm = new FakeLlm("weak", "best", "medium");
        var scores = new Dictionary<string, double> { ["weak"] = 0.2, ["best"] = 0.9, ["medium"] = 0.5 };

        var (best, score, all) = await Reasoning.BestOfNAsync(llm, "Write it.", candidate => scores[candidate], n: 3);

        Assert.Equal("best", best);
        Assert.Equal(0.9, score);
        Assert.Equal(new[] { 0.2, 0.9, 0.5 }, all);
    }

    [Fact]
    public void A_correct_roman_numeral_regex_scores_full_marks()
    {
        const string pattern = "(?=[MDCLXVI])M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})";

        Assert.Equal(1.0, Reasoning.ScoreRomanNumeralRegex(pattern));
    }

    [Fact]
    public void A_regex_in_code_fences_and_anchors_is_cleaned_first()
    {
        const string reply = "```regex\n^(?=[MDCLXVI])M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$\n```";

        Assert.Equal(1.0, Reasoning.ScoreRomanNumeralRegex(reply));
    }

    [Fact]
    public void A_partly_right_regex_gets_partial_credit()
    {
        var score = Reasoning.ScoreRomanNumeralRegex("[IVXLCDM]+");

        Assert.True(score > 0 && score < 1, $"expected partial credit, got {score}");
    }

    [Fact]
    public void An_invalid_regex_scores_zero()
    {
        Assert.Equal(0.0, Reasoning.ScoreRomanNumeralRegex("(unclosed"));
    }
}
