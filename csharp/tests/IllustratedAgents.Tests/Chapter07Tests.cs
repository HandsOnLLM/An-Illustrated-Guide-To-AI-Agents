namespace IllustratedAgents.Tests;

public class Chapter07Tests
{
    [Theory]
    [InlineData("J", "J", 1.0)]
    [InlineData("The answer is j.", "J", 1.0)]
    [InlineData("E) just under 1000 cc", "E", 1.0)]
    [InlineData("I", "J", 0.0)]
    [InlineData("I'm not sure.", "J", 0.0)]
    public async Task ExactMatch_compares_the_first_choice_letter(string prediction, string expected, double score)
    {
        Assert.Equal(score, await Scorers.ExactMatch(prediction, new Example("Q", Expected: expected)));
    }

    [Fact]
    public async Task Programmatic_uses_the_examples_own_check()
    {
        var noCommas = new Example("Write without commas.", Check: text => !text.Contains(','));

        Assert.Equal(1.0, await Scorers.Programmatic("No commas here", noCommas));
        Assert.Equal(0.0, await Scorers.Programmatic("One, two", noCommas));
    }

    [Theory]
    [InlineData("0.8", 0.8)]
    [InlineData("  1.0 because it matches", 1.0)]
    [InlineData("7", 1.0)]
    [InlineData("I'd say high.", 0.0)]
    public async Task Judge_reads_a_score_from_the_judge_model(string judgeReply, double score)
    {
        var judge = new FakeLlm(judgeReply);

        var result = await Scorers.Judge(judge)("the cranial cavity", new Example("Q", Expected: "the cranial cavity"));

        Assert.Equal(score, result);
    }

    [Fact]
    public async Task Judge_prompt_contains_expected_and_response()
    {
        var judge = new FakeLlm("1.0");

        await Scorers.Judge(judge)("about 950 cc", new Example("Q", Expected: "just under 1000 cc"));

        var prompt = judge.Calls[0][0].Content!;
        Assert.Contains("Expected: just under 1000 cc", prompt);
        Assert.Contains("Response: about 950 cc", prompt);
    }

    [Fact]
    public async Task Evaluator_uses_a_fresh_agent_for_every_example()
    {
        var created = 0;
        var evaluator = new Evaluator(() => { created++; return new StubAgent("J"); });
        var benchmark = new Benchmark("MMLU Pro", [new Example("Q1", "J"), new Example("Q2", "E"), new Example("Q3", "J")], Scorers.ExactMatch);

        await evaluator.RunAsync(benchmark);

        Assert.Equal(3, created);
    }

    [Fact]
    public async Task Evaluator_reports_every_prediction_and_the_pass_rate()
    {
        var evaluator = new Evaluator(() => new StubAgent("J"));
        var benchmark = new Benchmark("MMLU Pro", [new Example("Q1", "J"), new Example("Q2", "E"), new Example("Q3", "J"), new Example("Q4", "A")], Scorers.ExactMatch);

        var result = await evaluator.RunAsync(benchmark);

        Assert.Equal("MMLU Pro", result.Name);
        Assert.Equal(0.5, result.PassRate);
        Assert.Equal(4, result.Results.Count);
        Assert.Equal(new ExampleResult("J", 1.0), result.Results[0]);
        Assert.Equal(0.0, result.Results[1].Score);
    }

    [Fact]
    public async Task Evaluator_on_an_empty_benchmark_scores_zero()
    {
        var result = await new Evaluator(() => new StubAgent("x")).RunAsync(new Benchmark("Empty", [], Scorers.ExactMatch));

        Assert.Equal(0.0, result.PassRate);
        Assert.Empty(result.Results);
    }
}
