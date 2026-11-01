# Chapter 5 · Tools

Notebooks, in this order: [`chapter05.ipynb`](../../../chapter05/chapter05.ipynb), [`chapter05_mcp.ipynb`](../../../chapter05/chapter05_mcp.ipynb), [`chapter05_native_tool_calling.ipynb`](../../../chapter05/chapter05_native_tool_calling.ipynb), [`chapter05_skills.ipynb`](../../../chapter05/chapter05_skills.ipynb)

The biggest chapter. TinyAgent learns to use tools four ways: a JSON blob in its reply, tools served over MCP, native function calling, and skills loaded from SKILL.md files.

**Provided for you:** `ToolInvoker` calls a C# delegate with the model's JSON arguments, matched by name. It's C#'s answer to Python's `tool_func(**kwargs)`, and it's reflection plumbing rather than an agent concept. `McpServer` is the server side of MCP, the way the book uses a library for its server. You build the client.

## Part 1 · Text-based tools: `src/IllustratedAgents/Tools/Tools.cs`

| Member | Behavior |
| --- | --- |
| `AddTool(name, function, description)` | Registers the tool under its name. Registering the same name again replaces it. |
| `Descriptions` | One line per tool, in registration order: the name in backticks, a colon, then the description. |
| `Prompt` | A blank line, a `# Tools` heading, a sentence saying these are the only tools available, the descriptions, then the instruction to call a tool by replying with JSON: `{"tool": "name", "kwargs": {"param": "value"}}`. It ends with a blank line. |
| `Parse(response)` | If the content contains `"tool":`, takes the text from the first `{` to the last `}`, parses it as JSON (allowing trailing commas), and returns a new response with the same content, reasoning and metadata and that JSON as its tool call. Text without a tool call, or with JSON that won't parse, comes back unchanged. |
| `ExecuteAsync(response)` | Reads the tool name and `kwargs` from the tool call. An unknown tool returns `Tool '{name}' not found.` A tool listed in `RequiresApproval` asks the approver first; if denied, returns `Tool '{name}' was denied by the user.` Otherwise runs the tool through `ToolInvoker` and returns its result. If the tool throws, returns `Error running tool '{name}': {message}` instead, so the model can try again. Cancellation is never swallowed. |
| `Observation(result)` | Returns the role `user` and the text `OBSERVATION: ` followed by the result formatted with `ToolInvoker.Format`. |
| `IsDone(response)` | Done when there's no tool call. Also done when the tool is `final_answer`: its kwargs become the response's content. Kwargs are usually a string; if they're an object with a single string value, that value is the answer. Any other tool means not done. |

**Different from the book:** Python lets a failing tool crash the agent. Here the error goes back to the model as an observation. Koenigstein's *AI Agents: The Definitive Guide*, chapter 5, explains why that matters in production.

## Part 2 · The chapter 5 agent: `src/IllustratedAgents/Agents/Ch05.cs`

| Member | Behavior |
| --- | --- |
| `SystemPrompt` | `You are a helpful assistant.`, a blank line, then the tools' prompt. |
| `RunAsync(task)` | On the first run only, adds the system prompt to memory. (Python does this in the constructor, but a constructor can't await.) Then adds the task, starts a run, and takes one step. |
| `StepAsync()` | Sends memory and the tool schemas to the model. Adds the reply to memory as an assistant message, with its tool call. Parses the tool call. If done, records the answer and returns it. Otherwise executes the action. |
| `ExecuteActionAsync(response)` | Runs the tool, adds the observation to memory with the role the tools chose, records the step with its observation, and returns the observation. |

This agent takes exactly one step, so a run that uses a tool ends with the observation. Chapter 6 adds the loop.

## Part 3 · MCP: `src/IllustratedAgents/Mcp/McpClient.cs` and `McpTools.cs`

MCP over stdio is newline-delimited JSON-RPC 2.0. `RequestAsync` and `NotifyAsync` are provided: they send a message and wait for the matching response.

| Member | Behavior |
| --- | --- |
| `McpClient.InitializeAsync()` | Sends `initialize` with the protocol version, empty client capabilities, and client info naming TinyAgent. Stores the server's `serverInfo`, then sends the `notifications/initialized` notification. |
| `McpClient.ListToolsAsync()` | Sends `tools/list` and returns each tool's name, description and input schema. |
| `McpClient.CallToolAsync(name, arguments)` | Sends `tools/call` with the name and a copy of the arguments, and returns the text of the first content block. If the result is marked as an error, prefixes the text with `Error: `. |
| `McpTools.ConnectAsync(client)` | Lists the server's tools and registers each as a tool whose function forwards its arguments to `CallToolAsync`. A function whose only parameter is a `JsonObject` receives all the arguments at once, and a `CancellationToken` parameter is filled in automatically. |

## Part 4 · Native tool calling: `ToolSchema.cs` and `NativeTools.cs`

| Member | Behavior |
| --- | --- |
| `ToolSchema.JsonTypeOf(type)` | `string` → `string`; `bool` → `boolean`; `int`, `long`, `short` → `integer`; `double`, `float`, `decimal` → `number`; arrays and other collections → `array`; anything else → `object`. Nullable types use their underlying type. |
| `ToolSchema.FromDelegate(name, function, fallback)` | An OpenAI function definition: type `function`, the registered name, a description, and parameters as a JSON Schema object. Each parameter becomes a property with its JSON type, and with a description if it has a `[Description]` attribute. Parameters without a default value are required. `CancellationToken` parameters are left out. The description comes from a `[Description]` attribute on the method, or else the fallback. |
| `NativeTools.Schemas` | One schema per registered tool, in order. |
| `NativeTools.Prompt` | Empty: native tools need no instructions in the prompt. |
| `NativeTools.Parse(response)` | Without a tool call, returns the response unchanged. Otherwise reads the function name and its arguments (which may be a JSON string or an object; an empty string means no arguments) and returns a new response whose tool call is `{"tool": name, "kwargs": arguments}`. |
| `NativeTools.Observation(result)` | The role `tool` and the formatted result, with no prefix. |
| `NativeTools.IsDone(response)` | Done exactly when there's no tool call. |

**Different from the book:** Python reads the schema name from the function's own name. C# method names are PascalCase, and lambdas have compiler-generated names, so the schema uses the name you registered.

## Part 5 · Skills: `src/IllustratedAgents/Tools/Skills.cs`

| Member | Behavior |
| --- | --- |
| `ParseFrontmatter(text)` | Reads `key: value` lines into a dictionary, splitting at the first colon and trimming both sides. Lines without a colon are skipped. |
| `AddSkill(folder)` | Reads `SKILL.md` from the folder and splits it on `---` into at most three parts. A missing frontmatter block is a `FormatException`. Tier 1: the frontmatter's name, with the description `A skill. ` plus the frontmatter description. Tier 2: everything after the frontmatter, trimmed. Tier 3: the names of the folder's other files, sorted. Registers a tool with no parameters that returns the instructions, a blank line, `Skill folder:` with the folder's full path, a blank line, and `Available files:` with the file names in square brackets. |
| `Prompt` | Three lines: specialized skills are available; to activate one, call it with an empty argument object; skills return instructions and don't do the task themselves. |

## Done when

```
dotnet test --filter "FullyQualifiedName~Chapter05"
```

## Run it

```
ollama pull gemma3:12b
ollama pull gemma4:e4b
dotnet run --project chapters/Chapter05            # text-based tools
dotnet run --project chapters/Chapter05 mcp        # MCP server as a child process
dotnet run --project chapters/Chapter05 native     # native function calling
dotnet run --project chapters/Chapter05 skills     # SKILL.md
```

You can also point MCP Inspector at the server: `npx @modelcontextprotocol/inspector dotnet run --project chapters/Chapter05.McpServer`

## C# you'll use

- Delegates (`Delegate`, `Func<...>`) and method groups: passing a method as a value
- `OrderedDictionary<TKey, TValue>` (new in .NET 9) for a registry that keeps insertion order
- Attributes: `[Description]` and reading it with reflection
- `try` / `catch` with an exception filter (`when`)
- Tuples as return values: `(string Role, string Content)`
- File and directory APIs: `File.ReadAllText`, `DirectoryInfo.GetFiles`
- Later, swap the hand-written client for the official MCP C# SDK (`ModelContextProtocol` on NuGet). Building it by hand first shows you what the SDK does for you.
