# Chapter 9 · Multimodal Understanding

Notebook: [`chapter09.ipynb`](../../../chapter09/chapter09.ipynb)

TinyAgent can look at images. The model already can; you only need to put the image into the message the right way.

## What to build

### `src/IllustratedAgents/Memory/MultimodalMemory.cs` · `AddAsync(...)`

- Without image data, stores the message like plain memory does.
- With image data, stores a message whose parts are the image first, then the text.
  - Image data starting with `http://` or `https://` is used as the image URL as it is.
  - Anything else is base64. It becomes a data URL: `data:`, the image type, `;base64,`, then the data. The provided `GuessMimeType` picks `image/png` or `image/jpeg`.
- The tool call, if any, is kept either way.

`Llm.ToJson` already sends a message with parts as a content array, so the model server receives the image.

### `src/IllustratedAgents/Agents/Ch09.cs` · `TinyAgent.RunAsync(task, imageData)`

Runs the chapter 6 loop with the image passed along to memory. This agent inherits from the chapter 6 agent, whose `RunAsync` already accepts an image; this public method exposes it.

**Different from the book:** the Python memory always labels base64 data as JPEG (or PNG, in the notebook). This one checks the data's first bytes.

## Done when

```
dotnet test --filter "FullyQualifiedName~Chapter09"
```

## Run it

```
ollama pull gemma4:e4b
dotnet run --project chapters/Chapter09
```

## C# you'll use

- Inheritance across chapters: `Ch09.TinyAgent` extends `Ch06.TinyAgent` and calls its `protected` method
- The `new` modifier, for a method that deliberately hides an inherited one
- `Convert.ToBase64String` (used in the demo)
