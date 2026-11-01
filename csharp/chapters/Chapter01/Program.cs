// Chapter 1: the TinyAgent skeleton. No model yet, so this runs without Ollama.
using IllustratedAgents.Chapters.Ch01;

var agent = new TinyAgent();

Console.WriteLine(agent.Run("What is 2 + 2?"));
Console.WriteLine(agent.ExecuteAction("look up the weather"));
