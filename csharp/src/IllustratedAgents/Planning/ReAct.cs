using System.Text.RegularExpressions;

namespace IllustratedAgents;

/// <summary>
/// ReAct (Reason and Act) with text parsing: the model writes a THOUGHT and an ACTION each turn, and the
/// agent loops until the model calls <c>final_answer</c> or runs out of steps. Chapter 6.
/// </summary>
public class ReAct
{
    public ReAct(int maxSteps = 10) => MaxSteps = maxSteps;

    /// <summary>The most steps the agent may take before giving up.</summary>
    public int MaxSteps { get; }

    /// <summary>The ReAct instructions added to the system prompt. Provided: it's the book's prompt, verbatim.</summary>
    public virtual string Prompt => """

        # ReAct (Reason and Act)

        You are a ReAct agent that performs exactly ONE step per turn.

        ## ReAct Format

        You use the following format for each step:

        THOUGHT: [Your reasoning about what to do next]
        ACTION:
        {
            "tool": "a_tool_name",
            "kwargs": {"param": "value"},
        }

        An observation will be provided after each action. You do not generate the observation yourself.

        ## ReAct Completion

        To provide the final answer to the task, use an action blob with "tool": "final_answer" tool.
        It is the only way to complete the task, else you will be stuck on a loop.
        So your final output should look like this:

        ACTION:
        {
            "tool": "final_answer",
            "kwargs": "insert your final answer here"
        }

        Use the `final_answer` tool when you are completely done with all subtasks and have the final answer ready.
        You can also use `final_answer` to directly reply to a user's question without using any other tools.


        """;

    /// <summary>
    /// Split a ReAct reply into its THOUGHT (which becomes <see cref="Response.Reasoning"/>) and its ACTION
    /// (which becomes <see cref="Response.Content"/>). A missing section becomes an empty string.
    /// </summary>
    public virtual Response Parse(Response response)
    {
        var text = response.Content;

        // Each section runs until the next section starts, or to the end of the text
        var thought = Regex.Match(text, @"THOUGHT:\s*(.+?)(?=ACTION:|OBSERVATION:|$)", RegexOptions.Singleline);
        var action = Regex.Match(text, @"ACTION:\s*(.+?)(?=THOUGHT:|OBSERVATION:|$)", RegexOptions.Singleline);

        // Keep only the action as content
        response.Content = action.Success ? action.Groups[1].Value.Trim() : "";
        response.Reasoning = thought.Success ? thought.Groups[1].Value.Trim() : "";
        return response;
    }
}

/// <summary>ReAct for models with native reasoning and tool calling: no prompt, no parsing. Chapter 6.</summary>
public class NativeReAct : ReAct
{
    public NativeReAct(int maxSteps = 10) : base(maxSteps)
    {
    }

    public override string Prompt
    {
        get
        {
            return "";
        }
    }

    public override Response Parse(Response response)
    {
        return response;
    }
}
