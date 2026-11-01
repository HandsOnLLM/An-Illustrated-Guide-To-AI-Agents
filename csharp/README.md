# TinyAgent in C#

A C# version of the TinyAgent you build in *An Illustrated Guide to AI Agents*, chapter by chapter, as an exercise kit. Each chapter has a spec, a set of tests, and a console app that runs that chapter's notebook demos against your own model server.

It is built from scratch, like the book's Python: no agent framework and no NuGet packages in the library, just `HttpClient` and `System.Text.Json` against any OpenAI-compatible endpoint (Ollama, llama.cpp, LM Studio, vLLM, OpenRouter).

## Two branches

| Branch | What's in it |
| --- | --- |
| `csharp` | **The exercise kit.** Every type, signature and test is there, but each method you're meant to write throws `NotImplementedException` with the chapter and spec to read. |
| `csharp-solutions` | The same files with every method written. Use it to check your work once you've passed a chapter's tests, or when you're properly stuck. |

The two branches differ only inside those method bodies, so comparing one file shows exactly one chapter's answer:

```
git diff csharp csharp-solutions -- csharp/src/IllustratedAgents/Tools/Tools.cs
```

## What you need

- The [.NET 10 SDK](https://dotnet.microsoft.com/download/dotnet/10.0)
- [Ollama](https://ollama.com), or any OpenAI-compatible server, for the demos. The tests need no model at all.
- The models the book uses: `ollama pull gemma3:12b`, `ollama pull gemma4:e4b`, `ollama pull gemma4:e2b`, `ollama pull embeddinggemma`

The demos read three optional environment variables, so you can point them anywhere without editing code:

| Variable | Default |
| --- | --- |
| `TINYAGENT_MODEL` | the model the book uses for that chapter |
| `TINYAGENT_BASE_URL` | `http://localhost:11434/v1` |
| `TINYAGENT_API_KEY` | `no_key` |

## How to work a chapter

1. Read the chapter in the book and skim its notebook.
2. Read the spec: `chapters/ChapterNN/README.md`. It describes the behavior, never the code.
3. Fill in the methods it names in `src/IllustratedAgents`.
4. Run the chapter's tests until they pass: `dotnet test --filter "FullyQualifiedName~ChapterNN"`
5. Run the chapter's demo against your model: `dotnet run --project chapters/ChapterNN`
6. Compare with `csharp-solutions` if you want a second opinion.

Chapters build on each other, so work them in order. The tests use a scripted fake model, so they're fast and give the same result every time.

## Chapters

| Chapter | You build | Demo |
| --- | --- | --- |
| [1 · Introduction](chapters/Chapter01/README.md) | The TinyAgent skeleton | `dotnet run --project chapters/Chapter01` |
| [2 · Large language models](chapters/Chapter02/README.md) | `Llm`, `Response`, `Trajectory`, an agent with a model | `dotnet run --project chapters/Chapter02` |
| [3 · Reasoning](chapters/Chapter03/README.md) | Self-consistency and best-of-N | `dotnet run --project chapters/Chapter03` |
| [4 · Memory](chapters/Chapter04/README.md) | `Memory`, trimming, summarization, RAG, embeddings | `… Chapter04 [short-term \| long-term]` |
| [5 · Tools](chapters/Chapter05/README.md) | Text tools, MCP client, native tool calling, skills | `… Chapter05 [mcp \| native \| skills]` |
| [6 · Planning](chapters/Chapter06/README.md) | ReAct, NativeReAct, the autonomy loop, Plan-and-Solve, Reflexion | `… Chapter06 [native \| plan \| skills]` |
| [7 · Evaluation](chapters/Chapter07/README.md) | Evaluator, exact match, programmatic checks, LLM judge | `dotnet run --project chapters/Chapter07` |
| [8 · Multi-agent](chapters/Chapter08/README.md) | Agents as tools, an orchestrator | `dotnet run --project chapters/Chapter08` |
| [9 · Multimodal](chapters/Chapter09/README.md) | Image memory, an agent that sees | `dotnet run --project chapters/Chapter09` |
| [10 · Coding agents](chapters/Chapter10/README.md) | Workspace-locked code tools, the finished agent with a display | `dotnet run --project chapters/Chapter10` |

## Layout

```
csharp/
├── IllustratedAgents.sln
├── src/IllustratedAgents/          the library: the C# version of src/illustrated_agents
│   ├── Llm/                        Llm, EmbeddingModel, ChatMessage, Response
│   ├── Memory/                     Memory and its four variants
│   ├── Tools/                      Tools, NativeTools, Skills, ToolSchema, ToolInvoker
│   ├── Mcp/                        McpClient, McpTools, McpServer
│   ├── Planning/                   ReAct, NativeReAct, PlanAndSolve, Reflexion
│   ├── Reasoning/                  chapter 3's techniques
│   ├── Evaluation/                 chapter 7's evaluator and scorers
│   ├── Agents/                     each chapter's TinyAgent, as the Python chapters/ folder has them
│   ├── TinyAgent.cs                the finished agent
│   ├── Toolbox.cs, CodeTools.cs    the tools from the book
│   └── skills/file_analyzer/       the example skill
├── tests/IllustratedAgents.Tests/  one test class per chapter
└── chapters/ChapterNN/             a spec and a demo app per chapter (plus the chapter 5 MCP server)
```

Each chapter's agent lives in its own namespace, `IllustratedAgents.Chapters.ChNN`, just as the Python repo keeps `chapters/chN.py`. The finished agent is `IllustratedAgents.TinyAgent`. Because they share a name, a file that uses a chapter's agent says which one it means.

## Provided for you

Some code isn't an agent concept, so it's written already:

- `ToolInvoker`: calls a C# method with the model's JSON arguments. It's reflection plumbing, C#'s answer to Python's `**kwargs`.
- `Llm.ToJson`: turns a message into the API's JSON shape.
- `McpServer`, and `McpClient.RequestAsync` and `NotifyAsync`: the JSON-RPC plumbing. You write the MCP client's protocol steps.
- `Toolbox`, the ReAct prompt, `ConsoleDisplay` and `TrajectoryView`.

## How it differs from the Python

The C# follows the book's design closely. Where it differs, it's for one of three reasons: C# requires it, .NET does it better, or a production agent needs it. Each spec says so where it applies.

- **Async throughout.** Model calls are `async`, so memory's `AddAsync` and the agents' `RunAsync` are too. A constructor can't await, so agents add their system prompt on the first run, and `RagMemory` is built with `CreateAsync`.
- **Typed messages.** `ChatMessage` and `Response` replace dicts. Tool calls stay as JSON (`JsonObject`), as the API sends them.
- **Tool errors don't crash the agent.** A tool that throws, or an unknown tool, becomes an observation the model can recover from. Malformed tool-call JSON is treated as plain text.
- **Tool schemas use the registered name**, since C# method names are PascalCase and lambdas have generated names. Descriptions come from `[Description]` attributes, the C# version of docstrings.
- **The MCP client is written by hand** so you can see the protocol. The Python uses the official package; in .NET, the official MCP C# SDK is the next step.
- **Chapter 3's best-of-N** verifies a regular expression rather than running generated code.
- **Chapter 10 runs C#**, through .NET 10 file-based apps, instead of Python.
