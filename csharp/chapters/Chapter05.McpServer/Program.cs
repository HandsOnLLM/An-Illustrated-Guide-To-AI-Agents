// Chapter 5: an MCP server with one tool, read_markdown, over stdio.
// The chapter 5 app starts this process itself; you can also test it with MCP Inspector:
//   npx @modelcontextprotocol/inspector dotnet run --project chapters/Chapter05.McpServer
// Anything this program writes to standard output must be a protocol message, so it never uses Console.WriteLine.
using IllustratedAgents;

var server = new McpServer("file_reader");
server.AddTool("read_markdown", Toolbox.ReadMarkdown);
await server.RunStdioAsync();
