# Chapter 1 · Introduction to AI Agents

Notebook: [`chapter01.ipynb`](../../../chapter01/chapter01.ipynb)

You build the TinyAgent skeleton: an agent with four empty slots (model, memory, tools, planner) and a `Run` method that doesn't do anything clever yet. Every later chapter fills in one slot.

## What to build

File: `src/IllustratedAgents/Agents/Ch01.cs`, class `TinyAgent`

| Member | Behavior |
| --- | --- |
| `Run(task)` | Runs the agent on a task by taking a single step and returning that step's result. |
| `Step(task)` | Returns the text `Received: ` followed by the task. |
| `ExecuteAction(action)` | A placeholder for later chapters. Returns `Executed action: ` followed by the action. |

The four slot properties are already declared and stay `null`.

## Done when

```
dotnet test --filter "FullyQualifiedName~Chapter01"
```

## Run it

```
dotnet run --project chapters/Chapter01
```

No model needed for this chapter.

## C# you'll use

- Classes, methods and string interpolation (Player's Guide, the early levels)
- The difference between a public method and a private one: `Step` is private, so only `Run` can call it
