// Chapter 3: reasoning. Chain-of-thought prompting, self-consistency, best-of-N and native reasoning.
// Needs `ollama pull gemma3:12b` and `ollama pull gemma4:e2b` (or set TINYAGENT_MODEL).
using IllustratedAgents;
using TinyAgent = IllustratedAgents.Chapters.Ch02.TinyAgent;

var llm = Llm.FromEnvironment("gemma3:12b", temperature: 1);
const string query = "I saw 9 penquins. 2 slid in the water and disappeared from sight whilst 4 waddled up from the shore. How many can I see?";

// 1. Few-shot, answer only
Console.WriteLine("── Few-shot");
Console.WriteLine((await llm.GenerateAsync(
[
    new ChatMessage("user", "I saw 6 flamingos. 2 flew away. 1 hid behind a tree. How many can I see? Be concise."),
    new ChatMessage("assistant", "3"),
    new ChatMessage("user", query),
])).Content);

// 2. Few-shot chain-of-thought: the example shows its working
Console.WriteLine("\n── Few-shot chain-of-thought");
Console.WriteLine((await llm.GenerateAsync(
[
    new ChatMessage("user", "I saw 6 flamingos. 2 flew away. 1 hid behind a tree. How many can I see?"),
    new ChatMessage("assistant", "You saw 6 flamingos 2 flew away. 6 - 2 = 4. Then, 1 flamingo hid. You see now 4 - 1 = 3."),
    new ChatMessage("user", query),
])).Content);

// 3. Zero-shot chain-of-thought, through the chapter 2 agent
Console.WriteLine("\n── Zero-shot chain-of-thought");
var agent = new TinyAgent(llm);
Console.WriteLine(await agent.RunAsync(query + " Let's think step by step."));

// 4. Self-consistency: ask ten times, take the most common answer
Console.WriteLine("\n── Self-consistency");
const string puzzle = """
    Six friends (Maarten, Ilse, Sarah, Jor, Irene, and Chris) are sitting in a row.

    - Sarah is in seat 3.
    - Chris is sitting at one of the ends of the row.
    - Jor is sitting immediately to the right of Chris.
    - Ilse is sitting exactly in the middle of Sarah and Maarten.
    - Irene is not sitting next to Sarah.
    - Maarten is sitting somewhere to the left of Irene.

    In which seat is Maarten sitting?
    Let's think step by step and give back your answer only after 'Answer:'.
    """;
var (answer, votes) = await Reasoning.SelfConsistencyAsync(llm, puzzle, samples: 10);
Console.WriteLine($"Majority answer: {answer}");
Console.WriteLine("Votes: " + string.Join(", ", votes.Select(v => $"{v.Key} × {v.Value}")));

// 5. Best-of-N with a verifier: the model writes a regex, the verifier tests it
Console.WriteLine("\n── Best-of-N");
const string regexTask = """
    Write a single regular expression that matches valid Roman numerals from 1 to 3999 and nothing else.
    It must handle subtractive notation (IV, IX, XL, XC, CD, CM), reject invalid patterns like IIII or VV,
    and reject the empty string.

    Give only the regular expression, with no explanation or markdown formatting.
    """;
var (best, score, scores) = await Reasoning.BestOfNAsync(llm, regexTask, Reasoning.ScoreRomanNumeralRegex, n: 10);
Console.WriteLine("Scores: " + string.Join(", ", scores.Select(s => s.ToString("0.00"))));
Console.WriteLine($"Best ({score:0.00}): {best}");

// 6. Native reasoning: a thinking model returns its reasoning separately
Console.WriteLine("\n── Native reasoning");
var thinker = Llm.FromEnvironment("gemma4:e2b", think: true);
var response = await thinker.GenerateAsync([new ChatMessage("user", query)]);
Console.WriteLine($"Reasoning: {response.Reasoning}");
Console.WriteLine($"Answer:    {response.Content}");
