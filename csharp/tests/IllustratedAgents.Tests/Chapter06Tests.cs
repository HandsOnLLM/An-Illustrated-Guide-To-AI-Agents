namespace IllustratedAgents.Tests;

using TinyAgent = IllustratedAgents.Chapters.Ch06.TinyAgent;

public class Chapter06Tests
{
    private static Tools ArithmeticTools(Tools? tools = null)
    {
        tools ??= new Tools();
        tools.AddTool("add", Toolbox.Add, "add(a: str, b: str)");
        tools.AddTool("subtract", Toolbox.Subtract, "subtract(a: str, b: str)");
        tools.AddTool("multiply", Toolbox.Multiply, "multiply(a: str, b: str)");
        return tools;
    }

    [Fact]
    public void ReAct_splits_thought_from_action()
    {
        var response = new Response
        {
            Content = """
                THOUGHT: I need to add first.
                ACTION:
                {"tool": "add", "kwargs": {"a": "4.6", "b": "6.685"}}
                """,
        };

        var parsed = new ReAct().Parse(response);

        Assert.Equal("I need to add first.", parsed.Reasoning);
        Assert.Equal("""{"tool": "add", "kwargs": {"a": "4.6", "b": "6.685"}}""", parsed.Content);
    }

    [Fact]
    public void ReAct_stops_a_section_at_a_made_up_observation()
    {
        var response = new Response { Content = "THOUGHT: go\nACTION: {\"tool\": \"add\"}\nOBSERVATION: 11.285" };

        Assert.Equal("{\"tool\": \"add\"}", new ReAct().Parse(response).Content);
    }

    [Fact]
    public void ReAct_without_sections_gives_empty_strings()
    {
        var parsed = new ReAct().Parse(new Response { Content = "Just chatting." });

        Assert.Equal("", parsed.Reasoning);
        Assert.Equal("", parsed.Content);
    }

    [Fact]
    public void ReAct_prompt_explains_the_format_and_final_answer()
    {
        var prompt = new ReAct().Prompt;

        Assert.Contains("THOUGHT:", prompt);
        Assert.Contains("\"tool\": \"final_answer\"", prompt);
        Assert.Equal(10, new ReAct().MaxSteps);
    }

    [Fact]
    public void NativeReAct_has_no_prompt_and_changes_nothing()
    {
        var react = new NativeReAct(maxSteps: 4);
        var response = new Response { Content = "THOUGHT: x\nACTION: y" };

        Assert.Equal("", react.Prompt);
        Assert.Same(response, react.Parse(response));
        Assert.Equal("THOUGHT: x\nACTION: y", response.Content);
        Assert.Equal(4, react.MaxSteps);
    }

    [Fact]
    public async Task Agent_system_prompt_is_planner_then_tools()
    {
        var agent = new TinyAgent(new FakeLlm("ACTION: {\"tool\": \"final_answer\", \"kwargs\": \"hi\"}"), new Memory(), ArithmeticTools(), new ReAct());

        await agent.RunAsync("Hi");

        var system = agent.Memory.GetMessages()[0].Content!;
        Assert.True(system.IndexOf("# ReAct") < system.IndexOf("# Tools"), "the planner's prompt should come first");
    }

    [Fact]
    public async Task Agent_loops_through_tools_until_final_answer()
    {
        var llm = new FakeLlm(
            "THOUGHT: Add first.\nACTION:\n{\"tool\": \"add\", \"kwargs\": {\"a\": \"4.6\", \"b\": \"6.685\"}}",
            "THOUGHT: Now multiply.\nACTION:\n{\"tool\": \"multiply\", \"kwargs\": {\"a\": \"11.285\", \"b\": \"4\"}}",
            "THOUGHT: Now subtract.\nACTION:\n{\"tool\": \"subtract\", \"kwargs\": {\"a\": \"45.14\", \"b\": \"3.14\"}}",
            "THOUGHT: Done.\nACTION:\n{\"tool\": \"final_answer\", \"kwargs\": \"42\"}");
        var agent = new TinyAgent(llm, new Memory(), ArithmeticTools(), new ReAct());

        var answer = await agent.RunAsync("What is (4.6 + 6.685) x 4, and then subtract 3.14 from the result?");

        Assert.Equal("42", answer);
        var steps = agent.Trajectory.LastRun!.Steps;
        Assert.Equal(4, steps.Count);
        Assert.Equal("Add first.", steps[0].Thought);
        Assert.Equal("OBSERVATION: 11.285", steps[0].Observation);
        Assert.Equal("42", steps[3].Answer);
        Assert.Contains(agent.Memory.GetMessages(), m => m.Content == "OBSERVATION: 45.14");
    }

    [Fact]
    public async Task Agent_with_native_tools_loops_on_tool_calls()
    {
        var llm = new FakeLlm()
            .ThenToolCall("add", """{"a": "4.6", "b": "6.685"}""", reasoning: "Add first.")
            .Then("The answer is 11.285.");
        var agent = new TinyAgent(llm, new Memory(), ArithmeticTools(new NativeTools()), new NativeReAct());

        var answer = await agent.RunAsync("What is 4.6 + 6.685?");

        Assert.Equal("The answer is 11.285.", answer);
        Assert.Equal("11.285", agent.Trajectory.LastRun!.Steps[0].Observation);
        Assert.Equal("Add first.", agent.Trajectory.LastRun.Steps[0].Thought);
    }

    [Fact]
    public async Task Agent_gives_up_after_max_steps()
    {
        var replies = Enumerable.Repeat("ACTION: {\"tool\": \"add\", \"kwargs\": {\"a\": \"1\", \"b\": \"1\"}}", 3).ToArray();
        var agent = new TinyAgent(new FakeLlm(replies), new Memory(), ArithmeticTools(), new ReAct(maxSteps: 3));

        Assert.Equal(TinyAgent.MaxStepsMessage, await agent.RunAsync("Loop forever"));
        Assert.Equal(3, agent.Trajectory.LastRun!.Steps.Count);
    }

    [Fact]
    public void PlanAndSolve_registers_its_planning_tools()
    {
        var tools = new Tools();

        var planner = new PlanAndSolve(tools);

        Assert.Contains("update_plan", tools.Registry.Keys);
        Assert.Contains("mark_done", tools.Registry.Keys);
        Assert.Contains("## Planning", planner.Prompt);
        Assert.Contains("# ReAct", planner.Prompt);
    }

    [Fact]
    public void PlanAndSolve_keeps_a_checklist()
    {
        var planner = new PlanAndSolve(new Tools());

        Assert.Equal("Plan updated:\n[ ] 1. Add\n[ ] 2. Multiply", planner.UpdatePlan(["Add", "Multiply"]));
        Assert.Equal("Plan:\n[x] 1. Add\n[ ] 2. Multiply", planner.MarkDone(1));
        Assert.Equal("There is no sub-task 5. The plan has 2.", planner.MarkDone(5));
    }

    [Fact]
    public async Task PlanAndSolve_tools_work_through_the_registry()
    {
        var tools = new Tools();
        var planner = new PlanAndSolve(tools);

        await tools.ExecuteAsync(new Response { ToolCall = System.Text.Json.Nodes.JsonNode.Parse("""{"tool": "update_plan", "kwargs": {"items": ["Add", "Multiply"]}}""")!.AsObject() });
        await tools.ExecuteAsync(new Response { ToolCall = System.Text.Json.Nodes.JsonNode.Parse("""{"tool": "mark_done", "kwargs": {"index": "2"}}""")!.AsObject() });

        Assert.Equal("[ ] 1. Add\n[x] 2. Multiply", planner.Render());
    }

    [Fact]
    public async Task Reflexion_critiques_on_every_interval_step_only()
    {
        var llm = new FakeLlm("You skipped the subtraction.");
        var reflexion = new Reflexion(llm, interval: 3);
        var memory = new Memory();
        await memory.AddAsync("user", "Do the sum.");

        await reflexion.ReflectAsync(memory, step: 0);
        await reflexion.ReflectAsync(memory, step: 2);
        await reflexion.ReflectAsync(memory, step: 3);

        Assert.Single(llm.Calls);
        Assert.Equal("system", llm.Calls[0][0].Role);
        Assert.Equal("[Reflection] You skipped the subtraction.", memory.GetMessages()[^1].Content);
    }
}
