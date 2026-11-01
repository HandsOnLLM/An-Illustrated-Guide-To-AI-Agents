# Chapter 8 · Multi-Agent Collaboration

Notebook: [`chapter08.ipynb`](../../../chapter08/chapter08.ipynb)

Agents as tools: two specialists, each a full chapter 6 agent with its own tools and memory, and an orchestrator whose only tools are "ask the math agent" and "ask the date agent". No new library classes, just a new way of putting the existing ones together.

## What to build

File: `src/IllustratedAgents/Agents/Ch08.cs`, static class `Team`

| Member | Behavior |
| --- | --- |
| `CreateMathAgent(llm)` | A chapter 6 agent with fresh memory, `NativeReAct`, and native tools `add`, `subtract` and `multiply` from the `Toolbox`. |
| `CreateDateAgent(llm)` | The same, with the native tools `today` and `days_between`. |
| `CreateOrchestrator(llm, mathAgent, dateAgent)` | A chapter 6 agent with fresh memory, `NativeReAct`, and two native tools. `ask_math_agent` takes a `question`, runs the math agent on it, and returns its answer. Its description is `Delegate to the math specialist.` `ask_date_agent` does the same with the date agent; its description is `Ask queries to a sub-Agent that handles ISO dates.` The specialists are passed in as `IAgent`, so any agent, or a test stub, can stand in. |

Each tool's only parameter the model sees is `question`. If your tool function also takes a `CancellationToken`, the invoker fills it in and the schema leaves it out.

## Done when

```
dotnet test --filter "FullyQualifiedName~Chapter08"
```

## Run it

```
ollama pull gemma4:e4b
dotnet run --project chapters/Chapter08
```

The demo prints three trajectories: the orchestrator's, and one for each specialist it called.

## C# you'll use

- Interfaces: the orchestrator depends on `IAgent`, not on a concrete class
- Lambdas that capture variables (closures): each tool remembers which agent it calls
- Namespaces: `IllustratedAgents.TinyAgent` (chapter 10) and `IllustratedAgents.Chapters.Ch06.TinyAgent` share a name, so you'll need to say which one you mean
