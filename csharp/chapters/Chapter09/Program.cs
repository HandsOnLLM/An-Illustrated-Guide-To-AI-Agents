// Chapter 9: multimodal understanding. The agent looks at a book cover.
// Needs a vision-capable model: `ollama pull gemma4:e4b` (or set TINYAGENT_MODEL).
using IllustratedAgents;
using TinyAgent = IllustratedAgents.Chapters.Ch09.TinyAgent;

var agent = new TinyAgent(Llm.FromEnvironment("gemma4:e4b"), new MultimodalMemory(), new NativeTools(), new NativeReAct());

// Download the image and send it as base64, as the book does. A plain https URL works too.
using var http = new HttpClient();
var bytes = await http.GetByteArrayAsync("https://raw.githubusercontent.com/HandsOnLLM/Hands-On-Large-Language-Models/main/images/book_cover.png");
var imageData = Convert.ToBase64String(bytes);

Console.WriteLine(await agent.RunAsync("Which animal is on the cover of 'Hands-On Large Language Models'?", imageData));
Console.WriteLine();
TrajectoryView.PrintMessages(agent.Memory.GetMessages());
