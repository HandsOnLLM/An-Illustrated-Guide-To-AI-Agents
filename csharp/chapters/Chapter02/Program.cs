// Chapter 2: giving TinyAgent a brain.
// Needs a model server. By default: Ollama on localhost with `ollama pull gemma4:e4b`.
// Point elsewhere with TINYAGENT_MODEL, TINYAGENT_BASE_URL and TINYAGENT_API_KEY.
using IllustratedAgents;
using TinyAgent = IllustratedAgents.Chapters.Ch02.TinyAgent;

var llm = Llm.FromEnvironment("gemma4:e4b", think: false);

// 1. Call the model directly and look at the Response it returns
var response = await llm.GenerateAsync([new ChatMessage("user", "Hi! How's life?")]);
Console.WriteLine(response);
Console.WriteLine();

// 2. The same model inside TinyAgent
var agent = new TinyAgent(llm);
Console.WriteLine(await agent.RunAsync("What is 2 + 2?"));
Console.WriteLine();

// 3. What the agent recorded
TrajectoryView.Print(agent.Trajectory);
