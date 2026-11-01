# Chapter 10 · Coding Agents

Notebook: [`chapter10.ipynb`](../../../chapter10/chapter10.ipynb)

The finished TinyAgent, as a coding agent in your terminal. It reads and writes files and runs code, but only inside one workspace folder, and only after you approve anything that changes something.

## What to build

### `src/IllustratedAgents/CodeTools.cs`

Every path a tool receives goes through `SafePath` first.

| Member | Behavior |
| --- | --- |
| `SafePath(path)` | Combines the path with the workspace root and resolves it to a full path. Returns it if it's the root or inside the root. Throws `UnauthorizedAccessException` if it's anywhere else: `../`, an absolute path elsewhere, or a sibling folder whose name merely starts the same way as the root's. |
| `ReadFile(path)` | The file's text, or `Error: '{path}' not found.` |
| `ListFiles(directory)` | The folder's entries sorted by name, one per line, with `/` after folder names. An empty folder is `(empty)`; a missing one is `Error: '{directory}' is not a directory.` The directory defaults to the workspace root. |
| `WriteFile(path, content)` | Creates any missing folders, writes the file, and returns `Written to '{path}'.` |
| `RunCSharpAsync(code)` | Writes the code to `snippet.cs` in a new folder under `.snippets` in the workspace, with `#:property PublishAot=false` as its first line. Runs `dotnet run` on that file from the workspace. Gives up after 60 seconds, killing the process and returning `Error: Code execution timed out (60s limit).` On a non-zero exit code, returns the exit code, the output and the errors. Otherwise returns the trimmed output, or `(no output)`. |
| `CreateRegistry(approve)` | A `NativeTools` registry with `read_file`, `list_files`, `write_file` and `run_csharp`, in that order, where `write_file` and `run_csharp` require approval. |

**Different from the book:** the Python agent runs Python. This one runs C# using .NET 10 file-based apps, so it needs nothing beyond the SDK. The `PublishAot=false` line matters: file-based apps default to native AOT, which downloads an extra compiler package the first time.

### `src/IllustratedAgents/TinyAgent.cs` · the finished agent

The chapter 6 loop and step, unchanged, plus the display:

| Member | Behavior |
| --- | --- |
| `RunAsync(task, imageData)` | Exactly as chapter 6, with the image passed to memory as in chapter 9. |
| `StepAsync()` | Calls `Display.Thinking()` before asking the model and `Display.ShowResponse(response)` once the reply is in memory. Otherwise as chapter 6. |
| `ExecuteActionAsync(response)` | Calls `Display.ShowToolCall(response)` before running the tool and `Display.ShowObservation(observation)` after recording it. Otherwise as chapter 6. |

`Display` shows nothing by default, which is what tests and evaluations want. `ConsoleDisplay` (provided) prints each event in colour.

## Done when

```
dotnet test --filter "FullyQualifiedName~Chapter10"
dotnet test
```

The second command runs every chapter's tests. All green means you've rebuilt TinyAgent in C#.

## Run it

```
ollama pull gemma4:e4b
dotnet run --project chapters/Chapter10
```

Try "Write a program that prints the first ten Fibonacci numbers, save it as fib.cs, then run it." Everything it creates lands in `chapters/Chapter10/workspace`, which git ignores.

## C# you'll use

- `Path.GetFullPath`, `Path.Combine` and why string checks on paths need care
- `System.Diagnostics.Process` with redirected output, `WaitForExitAsync`, and killing a process tree
- `CancellationTokenSource.CancelAfter` for timeouts
- Why the approval rule lives in the tool registry, not in the prompt: a prompt can be talked out of a rule; code can't
