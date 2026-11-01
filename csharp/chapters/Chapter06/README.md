# Chapter 6 · Planning and Reflection

Notebooks: [`chapter06.ipynb`](../../../chapter06/chapter06.ipynb), then [`chapter06_native_react.ipynb`](../../../chapter06/chapter06_native_react.ipynb)

TinyAgent becomes autonomous: it loops THOUGHT, ACTION, OBSERVATION until it has an answer. You build ReAct both ways (text parsing, and native reasoning with native tools), plus two extensions from the chapter: Plan-and-Solve and Reflexion.

## What to build

### `src/IllustratedAgents/Planning/ReAct.cs`

The ReAct prompt is provided: it's the book's prompt, word for word.

| Member | Behavior |
| --- | --- |
| `ReAct.Parse(response)` | Finds the THOUGHT section and the ACTION section in the response's content. Each section starts after its label (and any whitespace) and runs until the next label (THOUGHT, ACTION or OBSERVATION) or the end of the text, across line breaks. Sets the response's reasoning to the trimmed THOUGHT and its content to the trimmed ACTION. A missing section becomes an empty string. Changes the response it was given and returns it. |
| `NativeReAct.Prompt` | Empty: the model reasons on its own. |
| `NativeReAct.Parse(response)` | Returns the same response, unchanged. |

### `src/IllustratedAgents/Agents/Ch06.cs` · `TinyAgent`

| Member | Behavior |
| --- | --- |
| `SystemPrompt` | `You are a helpful assistant.`, a blank line, the planner's prompt, then the tools' prompt. |
| `RunAsync(task, imageData)` | Adds the system prompt on the first run only. Adds the task to memory (passing the image along for chapter 9), starts a run, then steps up to the planner's `MaxSteps` times. As soon as a step returns an answer, returns it. If none does, returns `MaxStepsMessage`. |
| `StepAsync()` | Like chapter 5, with two changes: the planner parses the reply before the tools do, and after running a tool the step returns `null` so the loop carries on. |
| `ExecuteActionAsync(response)` | Runs the tool, adds the observation to memory, and records the step. |

### `src/IllustratedAgents/Planning/PlanAndSolve.cs`

| Member | Behavior |
| --- | --- |
| constructor | Registers two tools on the registry it's given: `update_plan` and `mark_done`, with the descriptions from the book. |
| `Prompt` | The ReAct prompt, then a `## Planning` section: for non-trivial tasks, call `update_plan` first, then `mark_done` as each sub-task finishes, and revise the plan when new information changes what's needed. |
| `UpdatePlan(items)` | Replaces the plan with the items, none done, and returns `Plan updated:` followed by the rendered plan on the next line. |
| `MarkDone(index)` | Marks item `index` (counting from 1) as done and returns `Plan:` followed by the rendered plan. An index outside the plan returns `There is no sub-task {index}. The plan has {count}.` |
| `Render()` | One line per item: `[x]` or `[ ]`, a space, the item's number, a full stop, a space, then the task. |

### `src/IllustratedAgents/Planning/Reflexion.cs` · `ReflectAsync(memory, step)`

Does nothing on step 0 or on any step that isn't a multiple of the interval. Otherwise sends the model a system message asking it to critique the agent's recent steps and suggest a course correction, followed by the last six messages in memory. Adds `[Reflection] ` plus the critique to memory as a user message.

**Stretch goal:** as in the Python version, the agent loop doesn't call Reflexion. Add an optional Reflexion to a copy of the chapter 6 agent and call it after each step.

## Done when

```
dotnet test --filter "FullyQualifiedName~Chapter06"
```

## Run it

```
ollama pull gemma3:12b
ollama pull gemma4:e4b
dotnet run --project chapters/Chapter06            # ReAct with text parsing
dotnet run --project chapters/Chapter06 native     # native reasoning and tool calling
dotnet run --project chapters/Chapter06 plan       # Plan-and-Solve
dotnet run --project chapters/Chapter06 skills     # the chapter 5 skill, finished by the loop
```

## C# you'll use

- `Regex.Match` with `RegexOptions.Singleline` and lookaheads
- `protected` members, which the chapter 9 agent will reuse by inheriting from this one
- A `for` loop with an early `return`
- Nullable return types: `string?` means "an answer, or nothing yet"
