// Chapter 7: evaluation with exact match, programmatic checks and an LLM judge.
// Needs `ollama pull gemma4:e4b`. The judge uses the same local model unless you set
// JUDGE_MODEL, JUDGE_BASE_URL and JUDGE_API_KEY (the book uses a hosted Gemini model).
using IllustratedAgents;
using TinyAgent = IllustratedAgents.Chapters.Ch06.TinyAgent;

var llm = Llm.FromEnvironment("gemma4:e4b");
IAgent CreateAgent() => new TinyAgent(llm, new Memory(), new NativeTools(), new NativeReAct());
var evaluator = new Evaluator(CreateAgent);

static void Report(EvaluationResult result)
{
    Console.WriteLine($"{result.Name}: pass rate {result.PassRate:P0}");
    foreach (var (prediction, score) in result.Results)
    {
        Console.WriteLine($"  {score:0.00}  {prediction.ReplaceLineEndings(" ")[..Math.Min(90, prediction.ReplaceLineEndings(" ").Length)]}");
    }
    Console.WriteLine();
}

// 1. Exact match on multiple choice (three questions from MMLU Pro)
var mmluPro = new Benchmark("MMLU Pro",
[
    new("""
        Which of the following is the body cavity that contains the pituitary gland?
        A) Ventral B) Dorsal C) Buccal D) Thoracic E) Pericardial F) Abdominal G) Spinal H) Pelvic I) Pleural J) Cranial
        Answer with only the letter.
        """, Expected: "J"),
    new("""
        What is the approximate mean cranial capacity of Homo erectus?
        A) 1200 cc B) under 650 cc C) 1700 cc D) 1350 cc E) just under 1000 cc F) 1500 cc G) under 500 cc H) about 800 cc I) just over 1100 cc J) about 900 cc
        Answer with only the letter.
        """, Expected: "E"),
    new("""
        According to Moore's "ideal utilitarianism," the right action is the one that brings about the greatest amount of:
        A) wealth. B) virtue. C) fairness. D) pleasure. E) peace. F) justice. G) happiness. H) power. I) good. J) knowledge.
        Answer with only the letter.
        """, Expected: "I"),
], Scorers.ExactMatch);
Report(await evaluator.RunAsync(mmluPro));

// 2. Programmatic checks on instruction following (three examples from IFEval)
var ifEval = new Benchmark("IFEval",
[
    new("Write me a funny song with less than 10 sentences for a proposal to build a new playground at my local elementary school.",
        Check: text => text.Count(c => c is '.' or '!' or '?') < 10),
    new("Write an ad copy for a new product, a digital photo frame that connects to your social media accounts and displays your photos. Respond with at most 150 words.",
        Check: text => text.Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries).Length <= 150),
    new("I am planning a trip to Japan, and I would like thee to write an itinerary for my journey in a Shakespearean style. You are not allowed to use any commas in your response.",
        Check: text => !text.Contains(',')),
], Scorers.Programmatic);
Report(await evaluator.RunAsync(ifEval));

// 3. LLM-as-a-judge on open answers
var judge = new Llm(
    model: Environment.GetEnvironmentVariable("JUDGE_MODEL") ?? llm.Model,
    baseUrl: Environment.GetEnvironmentVariable("JUDGE_BASE_URL") ?? llm.BaseUrl,
    apiKey: Environment.GetEnvironmentVariable("JUDGE_API_KEY") ?? llm.ApiKey);
var openAnswers = new Benchmark("MMLU Pro, open answers",
[
    new("Which body cavity contains the pituitary gland?", Expected: "the cranial cavity"),
    new("What is the approximate mean cranial capacity of Homo erectus?", Expected: "just under 1000 cc"),
    new("According to Moore's 'ideal utilitarianism,' the right action is the one that brings about the greatest amount of what?", Expected: "good"),
], Scorers.Judge(judge));
Report(await evaluator.RunAsync(openAnswers));
