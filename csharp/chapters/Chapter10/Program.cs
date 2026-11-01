// Chapter 10: a coding agent in your terminal. It can read, list and write files and run C# code,
// all inside ./workspace, and it asks before writing or running anything.
// Needs `ollama pull gemma4:e4b` (or set TINYAGENT_MODEL). Type exit or press Ctrl+C to quit.
using IllustratedAgents;

const string Name = """

    ██████ ██ ███  ██ ██  ██   ▄████▄  ▄████  ██████ ███  ██ ██████
      ██   ██ ██ ▀▄██  ▀██▀    ██▄▄██ ██  ▄▄▄ ██▄▄   ██ ▀▄██   ██
      ██   ██ ██   ██   ██     ██  ██  ▀███▀  ██▄▄▄▄ ██   ██   ██

    """;

var workspace = new CodeTools(Path.Combine(Directory.GetCurrentDirectory(), "workspace"));
var agent = new TinyAgent(
    Llm.FromEnvironment("gemma4:e4b", think: true),
    new Memory(),
    workspace.CreateRegistry(),
    new NativeReAct(),
    new ConsoleDisplay());

Console.WriteLine(Name);
Console.WriteLine($"Workspace: {workspace.Root}\n");

while (true)
{
    Console.Write("\u001b[36m▎\u001b[97;1m > \u001b[0m");
    var query = Console.ReadLine()?.Trim();
    if (string.IsNullOrEmpty(query) || query is "exit" or "quit")
    {
        break;
    }

    try
    {
        await agent.RunAsync(query);
    }
    catch (Exception ex)
    {
        Console.WriteLine($"ERROR: {ex.Message}\n");
    }
}
