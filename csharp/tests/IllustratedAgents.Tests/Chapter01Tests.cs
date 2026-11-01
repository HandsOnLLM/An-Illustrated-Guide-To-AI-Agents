namespace IllustratedAgents.Tests;

using TinyAgent = IllustratedAgents.Chapters.Ch01.TinyAgent;

public class Chapter01Tests
{
    [Fact]
    public void Run_echoes_the_task()
    {
        var agent = new TinyAgent();

        Assert.Equal("Received: What is 2 + 2?", agent.Run("What is 2 + 2?"));
    }

    [Fact]
    public void ExecuteAction_is_a_placeholder()
    {
        var agent = new TinyAgent();

        Assert.Equal("Executed action: search", agent.ExecuteAction("search"));
    }

    [Fact]
    public void Every_slot_starts_empty()
    {
        var agent = new TinyAgent();

        Assert.Null(agent.Llm);
        Assert.Null(agent.Memory);
        Assert.Null(agent.Tools);
        Assert.Null(agent.Planner);
    }
}
