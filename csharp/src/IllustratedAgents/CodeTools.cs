using System.ComponentModel;
using System.Diagnostics;

namespace IllustratedAgents;

/// <summary>
/// The coding agent's tools from chapter 10, locked to one workspace folder: read, list and write files,
/// and run C# code. Writing and running need a person's approval.
/// </summary>
/// <remarks>
/// The Python version runs Python. This one runs C# through .NET 10 file-based apps
/// (<c>dotnet run snippet.cs</c>), so it needs no extra packages. The first run of each snippet compiles it,
/// which takes a few seconds.
/// </remarks>
public sealed class CodeTools
{
    public CodeTools(string workspace)
    {
        Root = Path.GetFullPath(workspace);
        Directory.CreateDirectory(Root);
    }

    /// <summary>The folder the tools may touch. Nothing outside it is readable or writable.</summary>
    public string Root { get; }

    /// <summary>A native-tool registry with all four tools; write_file and run_csharp require approval.</summary>
    public NativeTools CreateRegistry(Func<string, bool>? approve = null)
    {
        var tools = new NativeTools(requiresApproval: ["write_file", "run_csharp"], approve: approve);
        tools.AddTool("read_file", ReadFile, "Read a file: read_file(path: str)");
        tools.AddTool("list_files", ListFiles, "List files: list_files(directory: str)");
        tools.AddTool("write_file", WriteFile, "Write a file: write_file(path: str, content: str)");
        tools.AddTool("run_csharp", RunCSharpAsync, "Run C# code: run_csharp(code: str)");
        return tools;
    }

    /// <summary>
    /// Resolve <paramref name="path"/> inside the workspace. A path that escapes it, such as
    /// <c>../secrets.txt</c> or an absolute path elsewhere, throws <see cref="UnauthorizedAccessException"/>.
    /// </summary>
    public string SafePath(string path)
    {
        var resolved = Path.GetFullPath(Path.Combine(Root, path));
        var rootWithSeparator = Root.EndsWith(Path.DirectorySeparatorChar) ? Root : Root + Path.DirectorySeparatorChar;
        if (resolved != Root && !resolved.StartsWith(rootWithSeparator, StringComparison.Ordinal))
        {
            throw new UnauthorizedAccessException($"Path '{path}' is outside the workspace.");
        }
        return resolved;
    }

    [Description("Read a file's contents.")]
    public string ReadFile(string path)
    {
        var target = SafePath(path);
        return File.Exists(target) ? File.ReadAllText(target) : $"Error: '{path}' not found.";
    }

    [Description("List files in a directory.")]
    public string ListFiles(string directory = ".")
    {
        var target = SafePath(directory);
        if (!Directory.Exists(target))
        {
            return $"Error: '{directory}' is not a directory.";
        }

        var entries = new DirectoryInfo(target).GetFileSystemInfos()
            .OrderBy(entry => entry.Name, StringComparer.Ordinal)
            .Select(entry => entry is DirectoryInfo ? entry.Name + "/" : entry.Name)
            .ToList();
        return entries.Count > 0 ? string.Join("\n", entries) : "(empty)";
    }

    [Description("Write content to a file.")]
    public string WriteFile(string path, string content)
    {
        var target = SafePath(path);
        Directory.CreateDirectory(Path.GetDirectoryName(target)!);
        File.WriteAllText(target, content);
        return $"Written to '{path}'.";
    }

    [Description("Run a complete C# program (top-level statements) and return its output.")]
    public async Task<string> RunCSharpAsync(string code, CancellationToken cancellationToken = default)
    {
        // Each snippet gets its own folder so file-based apps never see each other
        var folder = Path.Combine(Root, ".snippets", Guid.NewGuid().ToString("N")[..8]);
        Directory.CreateDirectory(folder);
        var file = Path.Combine(folder, "snippet.cs");

        // File-based apps default to native AOT, which downloads a compiler package on first use.
        // A normal JIT build needs nothing beyond the SDK and starts faster.
        await File.WriteAllTextAsync(file, "#:property PublishAot=false\n" + code, cancellationToken);

        var startInfo = new ProcessStartInfo("dotnet")
        {
            WorkingDirectory = Root,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
        };
        startInfo.ArgumentList.Add("run");
        startInfo.ArgumentList.Add(file);

        using var process = Process.Start(startInfo)!;
        var stdout = process.StandardOutput.ReadToEndAsync(cancellationToken);
        var stderr = process.StandardError.ReadToEndAsync(cancellationToken);

        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        timeout.CancelAfter(TimeSpan.FromSeconds(60));
        try
        {
            await process.WaitForExitAsync(timeout.Token);
        }
        catch (OperationCanceledException) when (!cancellationToken.IsCancellationRequested)
        {
            process.Kill(entireProcessTree: true);
            return "Error: Code execution timed out (60s limit).";
        }

        var output = (await stdout).Trim();
        if (process.ExitCode != 0)
        {
            return $"Exit code {process.ExitCode}\nSTDOUT:\n{output}\nSTDERR:\n{(await stderr).Trim()}".Trim();
        }
        return output.Length > 0 ? output : "(no output)";
    }
}
