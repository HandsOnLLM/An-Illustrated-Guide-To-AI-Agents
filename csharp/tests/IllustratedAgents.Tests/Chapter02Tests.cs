using System.Net;
using System.Text.Json.Nodes;

namespace IllustratedAgents.Tests;

using TinyAgent = IllustratedAgents.Chapters.Ch02.TinyAgent;

public class Chapter02Tests
{
    private const string ChatReply = """
        {
          "model": "gemma4:e4b",
          "choices": [{ "message": { "role": "assistant", "content": "Life is good!", "reasoning": "Be friendly." } }],
          "usage": { "prompt_tokens": 12, "completion_tokens": 5 }
        }
        """;

    private static (Llm Llm, FakeHttpHandler Http) CreateLlm(string reply = ChatReply, bool think = false, double? temperature = null)
    {
        var http = new FakeHttpHandler(reply);
        var llm = new Llm("gemma4:e4b", "http://localhost:11434/v1", "secret", think, temperature, new HttpClient(http));
        return (llm, http);
    }

    [Fact]
    public async Task Llm_posts_to_chat_completions_with_the_api_key()
    {
        var (llm, http) = CreateLlm();

        await llm.GenerateAsync([new ChatMessage("user", "Hi! How's life?")]);

        Assert.Equal(HttpMethod.Post, http.Request!.Method);
        Assert.Equal("http://localhost:11434/v1/chat/completions", http.Request.RequestUri!.ToString());
        Assert.Equal("Bearer secret", http.Request.Headers.Authorization!.ToString());
    }

    [Fact]
    public async Task Llm_sends_the_model_and_messages()
    {
        var (llm, http) = CreateLlm();

        await llm.GenerateAsync([new ChatMessage("user", "Hi! How's life?")]);

        var body = http.RequestJson;
        Assert.Equal("gemma4:e4b", body["model"]!.GetValue<string>());
        var message = body["messages"]![0]!;
        Assert.Equal("user", message["role"]!.GetValue<string>());
        Assert.Equal("Hi! How's life?", message["content"]!.GetValue<string>());
    }

    [Fact]
    public async Task Llm_turns_reasoning_off_unless_think_is_set()
    {
        var (quiet, quietHttp) = CreateLlm(think: false);
        var (thinking, thinkingHttp) = CreateLlm(think: true);

        await quiet.GenerateAsync([new ChatMessage("user", "Hi")]);
        await thinking.GenerateAsync([new ChatMessage("user", "Hi")]);

        Assert.Equal("none", quietHttp.RequestJson["reasoning_effort"]!.GetValue<string>());
        Assert.Equal("medium", thinkingHttp.RequestJson["reasoning_effort"]!.GetValue<string>());
    }

    [Fact]
    public async Task Llm_sends_temperature_and_tools_only_when_given()
    {
        var (plain, plainHttp) = CreateLlm();
        var (tuned, tunedHttp) = CreateLlm(temperature: 1);
        var tools = new JsonArray(new JsonObject { ["type"] = "function" });

        await plain.GenerateAsync([new ChatMessage("user", "Hi")]);
        await tuned.GenerateAsync([new ChatMessage("user", "Hi")], tools);

        Assert.False(plainHttp.RequestJson.ContainsKey("temperature"));
        Assert.False(plainHttp.RequestJson.ContainsKey("tools"));
        Assert.Equal(1.0, tunedHttp.RequestJson["temperature"]!.GetValue<double>());
        Assert.Single(tunedHttp.RequestJson["tools"]!.AsArray());
    }

    [Fact]
    public async Task Llm_returns_content_reasoning_and_metadata()
    {
        var (llm, _) = CreateLlm();

        var response = await llm.GenerateAsync([new ChatMessage("user", "Hi")]);

        Assert.Equal("Life is good!", response.Content);
        Assert.Equal("Be friendly.", response.Reasoning);
        Assert.Null(response.ToolCall);
        Assert.Equal(new ResponseMetadata("gemma4:e4b", 12, 5), response.Metadata);
    }

    [Fact]
    public async Task Llm_reads_reasoning_content_and_the_first_tool_call()
    {
        const string reply = """
            {
              "model": "m",
              "choices": [{ "message": {
                "content": null,
                "reasoning_content": "I should multiply.",
                "tool_calls": [
                  { "id": "a", "type": "function", "function": { "name": "multiply", "arguments": "{}" } },
                  { "id": "b", "type": "function", "function": { "name": "add", "arguments": "{}" } }
                ] } }],
              "usage": { "prompt_tokens": 1, "completion_tokens": 1 }
            }
            """;
        var (llm, _) = CreateLlm(reply);

        var response = await llm.GenerateAsync([new ChatMessage("user", "Hi")]);

        Assert.Equal("", response.Content);
        Assert.Equal("I should multiply.", response.Reasoning);
        Assert.Equal("multiply", response.ToolCall!["function"]!["name"]!.GetValue<string>());
    }

    [Fact]
    public async Task Llm_reports_server_errors()
    {
        var http = new FakeHttpHandler("""{"error":"model not found"}""", HttpStatusCode.NotFound);
        var llm = new Llm("missing", httpClient: new HttpClient(http));

        await Assert.ThrowsAsync<HttpRequestException>(() => llm.GenerateAsync([new ChatMessage("user", "Hi")]));
    }

    [Fact]
    public void Trajectory_records_an_answer_step()
    {
        var trajectory = new Trajectory();
        trajectory.Initialize("What is 2 + 2?");

        trajectory.Add(new Response { Content = "4", Reasoning = "Simple sum." });

        var run = Assert.Single(trajectory.Runs);
        Assert.Equal("What is 2 + 2?", run.Query);
        var step = Assert.Single(run.Steps);
        Assert.Equal("4", step.Answer);
        Assert.Equal("Simple sum.", step.Thought);
        Assert.Null(step.Action);
        Assert.Null(step.Observation);
    }

    [Fact]
    public void Trajectory_records_an_action_step_when_there_is_an_observation()
    {
        var trajectory = new Trajectory();
        trajectory.Initialize("Multiply");
        var response = new Response { ToolCall = new JsonObject { ["tool"] = "multiply" } };

        trajectory.Add(response, observation: "37.23");

        var step = Assert.Single(trajectory.Runs[0].Steps);
        Assert.Equal("multiply", step.Action!["tool"]!.GetValue<string>());
        Assert.Equal("37.23", step.Observation);
        Assert.Null(step.Answer);
        Assert.Equal("", step.Thought);
    }

    [Fact]
    public void Trajectory_starts_a_new_run_per_task()
    {
        var trajectory = new Trajectory();

        trajectory.Initialize("first");
        trajectory.Add(new Response { Content = "a" });
        trajectory.Initialize("second");
        trajectory.Add(new Response { Content = "b" });

        Assert.Equal(2, trajectory.Runs.Count);
        Assert.Equal("second", trajectory.LastRun!.Query);
        Assert.Equal(2, trajectory.Steps.Count());
    }

    [Fact]
    public async Task Agent_sends_the_task_and_returns_the_answer()
    {
        var llm = new FakeLlm("4");
        var agent = new TinyAgent(llm);

        var answer = await agent.RunAsync("What is 2 + 2?");

        Assert.Equal("4", answer);
        var message = Assert.Single(Assert.Single(llm.Calls));
        Assert.Equal("user", message.Role);
        Assert.Equal("What is 2 + 2?", message.Content);
    }

    [Fact]
    public async Task Agent_records_each_run()
    {
        var agent = new TinyAgent(new FakeLlm("4", "Hello"));

        await agent.RunAsync("What is 2 + 2?");
        await agent.RunAsync("Hi");

        Assert.Equal(2, agent.Trajectory.Runs.Count);
        Assert.Equal("Hello", agent.Trajectory.Runs[1].Steps[0].Answer);
    }

    [Fact]
    public async Task Agent_has_no_memory_between_runs()
    {
        var llm = new FakeLlm("Nice to meet you.", "I don't know.");
        var agent = new TinyAgent(llm);

        await agent.RunAsync("We are Maarten and Jay.");
        await agent.RunAsync("What are our names?");

        Assert.Single(llm.Calls[1]);
    }
}
