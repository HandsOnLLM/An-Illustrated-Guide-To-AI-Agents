# Chapter 2 · Large Language Models

Notebook: [`chapter02.ipynb`](../../../chapter02/chapter02.ipynb)

You give TinyAgent a brain. You write the wrapper that talks to any OpenAI-compatible model server, the `Response` it returns, and the `Trajectory` that records what the agent did.

## What to build

### `src/IllustratedAgents/Llm/Llm.cs` · `Llm.GenerateAsync(messages, tools)`

- Builds a JSON request body with the `model` and the `messages`. Use the provided `Llm.ToJson` to turn each `ChatMessage` into JSON.
- Adds `tools` only when some were passed.
- Sets `reasoning_effort` to `"medium"` when `Think` is on and `"none"` when it's off.
- Adds `temperature` only when one was set.
- POSTs the body to `{BaseUrl}/chat/completions` with an `Authorization: Bearer {ApiKey}` header.
- If the server answers with an error status, throws an `HttpRequestException` that includes the status code and the server's message.
- From the first choice's `message`, builds a `Response`:
  - `Content`: the message's content, or an empty string when it's missing or null
  - `Reasoning`: the message's `reasoning`, or else its `reasoning_content`
  - `ToolCall`: the first entry of `tool_calls`, if there is one (copy it, don't move it)
  - `Metadata`: the response's `model` and the `usage` token counts. Missing usage counts as zero.

### `src/IllustratedAgents/Trajectory.cs`

| Member | Behavior |
| --- | --- |
| `Initialize(query)` | Starts a new `Run` for the query. |
| `Add(response, observation)` | Adds a `Step` to the latest run. The step's `Thought` is the response's reasoning (empty if none) and its `Metadata` comes from the response. With an observation, the step is an action: it stores a copy of the tool call and the observation. Without one, it's the final answer: it stores the response's content. |

### `src/IllustratedAgents/Agents/Ch02.cs` · `TinyAgent`

| Member | Behavior |
| --- | --- |
| `RunAsync(task)` | Starts a run in the trajectory, then takes one step. |
| `StepAsync(task)` | Sends the task to the model as a single user message, records the response in the trajectory, and returns its content. No memory yet: every run starts from nothing. |

## Done when

```
dotnet test --filter "FullyQualifiedName~Chapter02"
```

## Run it

```
ollama pull gemma4:e4b
dotnet run --project chapters/Chapter02
```

## C# you'll use

- `HttpClient`, `HttpRequestMessage` and `StringContent` for the POST
- `System.Text.Json.Nodes`: `JsonObject`, `JsonArray`, `JsonNode.Parse`, and the indexer for reading nested values. A `JsonNode` can belong to only one parent, so use `DeepClone()` before putting a node somewhere new.
- `async` and `await`. Every network call in the kit is asynchronous.
- The `?.` and `??` operators for values that might be missing
