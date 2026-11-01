// Chapter 8: multi-agent collaboration. An orchestrator delegates to a math agent and a date agent.
// Needs `ollama pull gemma4:e4b` (or set TINYAGENT_MODEL).
using IllustratedAgents;
using IllustratedAgents.Chapters.Ch08;

var llm = Llm.FromEnvironment("gemma4:e4b", think: true);

var mathAgent = Team.CreateMathAgent(llm);
var dateAgent = Team.CreateDateAgent(llm);
var orchestrator = Team.CreateOrchestrator(llm, mathAgent, dateAgent);

Console.WriteLine(await orchestrator.RunAsync("If I save €4 per day until 2030, how much will I have?"));
Console.WriteLine();

Console.WriteLine("── Orchestrator");
TrajectoryView.Print(orchestrator.Trajectory);
Console.WriteLine("── Date agent");
TrajectoryView.Print(dateAgent.Trajectory);
Console.WriteLine("── Math agent");
TrajectoryView.Print(mathAgent.Trajectory);
