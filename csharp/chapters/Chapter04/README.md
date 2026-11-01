# Chapter 4 · Memory

Notebooks: [`chapter04.ipynb`](../../../chapter04/chapter04.ipynb), then [`chapter04_short_term_memory.ipynb`](../../../chapter04/chapter04_short_term_memory.ipynb) and [`chapter04_long_term_memory.ipynb`](../../../chapter04/chapter04_long_term_memory.ipynb)

TinyAgent remembers the conversation. Then you try two ways to keep that memory short (trimming and summarizing) and one way to give it knowledge it was never told (retrieval-augmented generation).

`AddAsync` is asynchronous in every memory class because two of them call a model while adding a message. The plain memory finishes straight away.

## What to build

### `src/IllustratedAgents/Memory/Memory.cs` · `Memory`

| Member | Behavior |
| --- | --- |
| `AddAsync(role, content, toolCall, imageData)` | Appends a message with the role, the content and the tool call, if any. Ignores `imageData`; that's chapter 9. |
| `GetMessages()` | Returns every message in the order it was added. |

### `src/IllustratedAgents/Agents/Ch04.cs` · `TinyAgent`

| Member | Behavior |
| --- | --- |
| `RunAsync(task)` | Adds the task to memory as a user message, starts a run, and takes one step. |
| `StepAsync()` | Sends everything in memory to the model, adds the reply to memory as an assistant message, records it in the trajectory, and returns its content. |

### `src/IllustratedAgents/Memory/TrimmingMemory.cs`

`AddAsync` adds the message as usual, then keeps every system message plus only the last four other messages (two turns), in their original order.

### `src/IllustratedAgents/Memory/SummarizationMemory.cs`

`AddAsync` adds the message as usual. When the message is from the assistant, it rebuilds memory as a summary:

- The current summary is the content of the system message, if there is one.
- The conversation is every other message as a line of `role: content`.
- It asks the model to update the summary with the new conversation and output only the summary.
- Memory becomes a single system message holding the model's reply.

### `src/IllustratedAgents/Memory/RagMemory.cs`

| Member | Behavior |
| --- | --- |
| `CreateAsync(embeddingModel, documents)` | Embeds every document once and returns a memory that holds the documents and their embeddings. (A constructor can't await, so this static method builds the object.) |
| `SearchAsync(query, k)` | Embeds the query and returns the `k` documents (default 3) whose embeddings are most similar to it, most similar first. |
| `Cosine(a, b)` | The cosine similarity of two vectors: their dot product divided by the product of their lengths. |
| `AddAsync(...)` | For user messages, searches for the most relevant documents and stores the message as `Context:`, the documents one per line, a blank line, then `Question:` and the original message. Other messages are stored unchanged. |

### `src/IllustratedAgents/Llm/EmbeddingModel.cs` · `EmbedAsync(text)`

POSTs the model name and the text as `input` to `{BaseUrl}/embeddings`, and returns the first embedding in the response's `data` as a `float[]`. Throws `HttpRequestException` on an error status.

## Done when

```
dotnet test --filter "FullyQualifiedName~Chapter04"
```

## Run it

```
ollama pull gemma3:12b
ollama pull embeddinggemma
dotnet run --project chapters/Chapter04               # conversation memory
dotnet run --project chapters/Chapter04 short-term    # trimming and summarization
dotnet run --project chapters/Chapter04 long-term     # RAG
```

## C# you'll use

- Inheritance with `virtual` and `override`, and calling `base.AddAsync`
- Static factory methods for objects that need async setup
- LINQ `Where`, `TakeLast`, `OrderByDescending`, `Take`, and collection expressions with the spread operator `..`
- Raw string literals (`"""`) for multi-line prompts
