# Chapter 7 · Evaluation

Notebook: [`chapter07.ipynb`](../../../chapter07/chapter07.ipynb)

You measure TinyAgent: run it over a benchmark and score every answer three ways. Exact match for multiple choice, a programmatic check for instruction following, and an LLM as the judge for open answers.

## What to build

File: `src/IllustratedAgents/Evaluation/Evaluator.cs`

The records (`Example`, `Benchmark`, `ExampleResult`, `EvaluationResult`) and the `Scorer` delegate are provided. A score runs from 0 (fail) to 1 (pass), so partial credit works too.

| Member | Behavior |
| --- | --- |
| `Evaluator.RunAsync(benchmark)` | For every example, in order: builds a fresh agent with the factory (so no example sees another's memory), runs it on the task, and scores the prediction with the benchmark's scorer. Returns the benchmark's name, the average score as the pass rate (0 when there are no examples), and each prediction with its score. |
| `Scorers.ExactMatch` | Finds the first standalone letter from A to J in the prediction, ignoring case. Scores 1 if it equals the expected answer, otherwise 0. No letter scores 0. |
| `Scorers.Programmatic` | Scores 1 if the example's own check accepts the prediction, otherwise 0. No check scores 0. |
| `Scorers.Judge(judge)` | Returns a scorer that asks the judge model to score the response from 0.0 to 1.0, given the expected answer and the response, replying with a single number. It reads the first word of the reply as a number, using invariant culture so a decimal point always works, and clamps it to between 0 and 1. A reply that isn't a number scores 0. |

**Different from the book:** the Python scorer for exact match crashes when no letter is found, and the judge crashes on a non-number reply. Here both score 0. An evaluation run should never die because of one strange answer.

## Done when

```
dotnet test --filter "FullyQualifiedName~Chapter07"
```

## Run it

```
ollama pull gemma4:e4b
dotnet run --project chapters/Chapter07
```

The judge uses your local model by default. To use a stronger hosted judge, as the book does, set `JUDGE_MODEL`, `JUDGE_BASE_URL` and `JUDGE_API_KEY`.

## C# you'll use

- Records and positional records
- Delegates as values: a scorer is a function, and `Judge` is a function that builds one
- `double.TryParse` with `CultureInfo.InvariantCulture`
- `Math.Clamp` and LINQ `Average`
