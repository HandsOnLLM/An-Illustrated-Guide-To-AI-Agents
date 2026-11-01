namespace IllustratedAgents.Tests;

using IllustratedAgents.Chapters.Ch08;

public class Chapter08Tests
{
    [Fact]
    public void Math_agent_has_the_arithmetic_tools()
    {
        var agent = Team.CreateMathAgent(new FakeLlm());

        Assert.Equal(new[] { "add", "subtract", "multiply" }, agent.Tools.Registry.Keys);
        Assert.IsType<NativeTools>(agent.Tools);
        Assert.IsType<NativeReAct>(agent.Planner);
    }

    [Fact]
    public void Date_agent_has_the_date_tools()
    {
        var agent = Team.CreateDateAgent(new FakeLlm());

        Assert.Equal(new[] { "today", "days_between" }, agent.Tools.Registry.Keys);
    }

    [Fact]
    public void Date_tools_compute_days_between_iso_dates()
    {
        Assert.Equal(366, Toolbox.DaysBetween("2028-01-01", "2029-01-01"));
        Assert.Matches(@"^\d{4}-\d{2}-\d{2}$", Toolbox.Today());
    }

    [Fact]
    public void Orchestrator_offers_the_specialists_as_tools()
    {
        var orchestrator = Team.CreateOrchestrator(new FakeLlm(), new StubAgent("4"), new StubAgent("2026-10-30"));

        Assert.Equal(new[] { "ask_math_agent", "ask_date_agent" }, orchestrator.Tools.Registry.Keys);
        var schema = orchestrator.Tools.Schemas![0]!["function"]!;
        Assert.Equal("ask_math_agent", schema["name"]!.GetValue<string>());
        Assert.Equal(new[] { "question" }, schema["parameters"]!["required"]!.AsArray().Select(n => n!.GetValue<string>()));
    }

    [Fact]
    public async Task Orchestrator_delegates_and_uses_the_specialists_answer()
    {
        var math = new StubAgent("1308");
        var date = new StubAgent("327");
        var llm = new FakeLlm()
            .ThenToolCall("ask_date_agent", """{"question": "How many days from today until 2030-01-01?"}""")
            .ThenToolCall("ask_math_agent", """{"question": "What is 327 times 4?"}""")
            .Then("You will have saved €1308.");
        var orchestrator = Team.CreateOrchestrator(llm, math, date);

        var answer = await orchestrator.RunAsync("If I save €4 per day until 2030, how much will I have?");

        Assert.Equal("You will have saved €1308.", answer);
        Assert.Equal(new[] { "How many days from today until 2030-01-01?" }, date.Tasks);
        Assert.Equal(new[] { "What is 327 times 4?" }, math.Tasks);
        var steps = orchestrator.Trajectory.LastRun!.Steps;
        Assert.Equal("327", steps[0].Observation);
        Assert.Equal("1308", steps[1].Observation);
    }

    [Fact]
    public async Task Specialists_keep_their_own_trajectories()
    {
        var mathLlm = new FakeLlm().ThenToolCall("multiply", """{"a": "327", "b": "4"}""").Then("1308");
        var math = Team.CreateMathAgent(mathLlm);
        var orchestratorLlm = new FakeLlm().ThenToolCall("ask_math_agent", """{"question": "327 x 4?"}""").Then("€1308");
        var orchestrator = Team.CreateOrchestrator(orchestratorLlm, math, new StubAgent("unused"));

        await orchestrator.RunAsync("How much?");

        Assert.Equal("1308", math.Trajectory.LastRun!.Steps[0].Observation);
        Assert.Equal("1308", orchestrator.Trajectory.LastRun!.Steps[0].Observation);
    }
}
