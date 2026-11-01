# Chapter 3 · Reasoning Large Language Models

Notebook: [`chapter03.ipynb`](../../../chapter03/chapter03.ipynb)

Few-shot prompting and chain-of-thought need no new code: they're just different messages, and the demo shows them. You build the two techniques that do: self-consistency and best-of-N.

## What to build

File: `src/IllustratedAgents/Reasoning/Reasoning.cs`, static class `Reasoning`

| Member | Behavior |
| --- | --- |
| `ExtractAnswer(text, marker)` | Returns what follows the last occurrence of the marker (default `Answer:`), with line breaks removed and surrounding spaces trimmed. Text without the marker is returned whole, trimmed. |
| `CountVotes(answers)` | Counts how often each answer appears and returns the answers with their counts, most common first. |
| `SelfConsistencyAsync(llm, query, samples)` | Asks the model the same question `samples` times, each time as a fresh single user message. Extracts each answer, counts the votes, and returns the most common answer together with all the votes. |
| `BestOfNAsync(llm, prompt, verify, n)` | Asks the model `n` times, scores every reply with `verify`, and returns the highest-scoring reply, its score, and every score in the order the replies came. |
| `ScoreRomanNumeralRegex(candidate)` | The verifier for the demo. Cleans the candidate with the provided `CleanPattern`, then requires it to match the whole string. Tests it against six valid numerals (`III`, `IV`, `IX`, `LVIII`, `MCMXCIV`, `MMMCMXCIX`), which must match, and six invalid ones (empty, `IIII`, `VV`, `IC`, `ABC`, `MMMM`), which must not. The score is the share of the twelve it gets right. A pattern that doesn't compile, or takes too long to match, scores 0. |

**Different from the book:** the Python best-of-N demo asks for a Python function and runs it with `exec`. Running generated C# needs a compiler at runtime, so the C# demo asks for a regular expression instead, which .NET can test directly. The technique is the same: generate several candidates and keep the one a verifier likes best.

## Done when

```
dotnet test --filter "FullyQualifiedName~Chapter03"
```

## Run it

```
ollama pull gemma3:12b
ollama pull gemma4:e2b
dotnet run --project chapters/Chapter03
```

Self-consistency needs varied answers, so the demo uses a temperature of 1.

## C# you'll use

- LINQ: `GroupBy`, `OrderByDescending`, `Count`, `MaxBy`, `Select`
- Tuples as return values, and deconstructing them at the call site
- `System.Text.RegularExpressions.Regex`, with a timeout so a bad pattern can't hang the program
- `Func<string, double>`: passing a function as an argument
