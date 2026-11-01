// Chapter 4: memory. Run with an argument to choose the demo:
//   dotnet run              conversation memory
//   dotnet run short-term   trimming and summarization
//   dotnet run long-term    retrieval-augmented generation (also needs `ollama pull embeddinggemma`)
// Needs `ollama pull gemma3:12b` (or set TINYAGENT_MODEL).
using IllustratedAgents;
using TinyAgent = IllustratedAgents.Chapters.Ch04.TinyAgent;

var llm = Llm.FromEnvironment("gemma3:12b");

switch (args.FirstOrDefault() ?? "memory")
{
    case "memory":
    {
        // Without memory the chapter 2 agent forgets your names
        var forgetful = new IllustratedAgents.Chapters.Ch02.TinyAgent(llm);
        await forgetful.RunAsync("Hi! We are Maarten and Jay, authors of 'An Illustrated Guide to AI Agents'.");
        Console.WriteLine($"Chapter 2 agent: {await forgetful.RunAsync("Hi! What are our names?")}\n");

        // With memory it remembers
        var agent = new TinyAgent(llm, new Memory());
        await agent.RunAsync("Hi! We are Maarten and Jay, authors of 'An Illustrated Guide to AI Agents'.");
        Console.WriteLine($"Chapter 4 agent: {await agent.RunAsync("Hi! What are our names?")}\n");
        TrajectoryView.PrintMessages(agent.Memory.GetMessages());
        break;
    }

    case "short-term":
    {
        Console.WriteLine("── Trimming memory: only the last two turns survive");
        var trimming = new TinyAgent(llm, new TrimmingMemory());
        await trimming.RunAsync("Hi! I'm reading 'An Illustrated Guide to AI Agents'.");
        await trimming.RunAsync("There are many flamingos in this book, why?");
        await trimming.RunAsync("What is 1+1?");
        await trimming.RunAsync("What is 2+2?");
        TrajectoryView.PrintMessages(trimming.Memory.GetMessages());

        Console.WriteLine("── Summarization memory: one running summary");
        var summarizing = new TinyAgent(llm, new SummarizationMemory(llm));
        Console.WriteLine(await summarizing.RunAsync("Hi, my name is Sarah. Why are flamingos pink?"));
        await summarizing.RunAsync("Tell me about yourself.");
        await summarizing.RunAsync("What is your favorite color?");
        await summarizing.RunAsync("Are you fully autonomous?");
        TrajectoryView.PrintMessages(summarizing.Memory.GetMessages());
        break;
    }

    case "long-term":
    {
        var embeddingModel = new EmbeddingModel("embeddinggemma",
            Environment.GetEnvironmentVariable("TINYAGENT_BASE_URL") ?? "http://localhost:11434/v1");

        // Similar sentences point in similar directions
        var a = await embeddingModel.EmbedAsync("I love flamingos.");
        var b = await embeddingModel.EmbedAsync("Dolphins use echolocation.");
        var c = await embeddingModel.EmbedAsync("Flamingos are pink birds.");
        Console.WriteLine($"'I love flamingos.' vs 'Dolphins use echolocation.': {RagMemory.Cosine(a, b):0.000}");
        Console.WriteLine($"'I love flamingos.' vs 'Flamingos are pink birds.':  {RagMemory.Cosine(a, c):0.000}\n");

        string[] documents =
        [
            "Sarah works as a marine biologist studying coral reefs.",
            "Sarah lives in Lisbon, Portugal.",
            "Sarah's favorite hobby is rock climbing.",
            "Sarah favorite animals are flamingos.",
            "Sarah speaks fluent Spanish and Portuguese.",
            "Ilse is a software engineer at a renewable energy startup.",
            "Ilse lives in Amsterdam, the Netherlands.",
            "Ilse plays the cello in a local string quartet.",
            "Ilse's favorite author is Brandon Sanderson.",
            "Ilse's favorite animals are dolphins.",
        ];
        var memory = await RagMemory.CreateAsync(embeddingModel, documents);
        var agent = new TinyAgent(llm, memory);
        Console.WriteLine(await agent.RunAsync("What is Sarah's favorite animal?"));
        Console.WriteLine();
        TrajectoryView.PrintMessages(agent.Memory.GetMessages());
        break;
    }

    default:
        Console.WriteLine("Choose one: memory, short-term, long-term");
        break;
}
