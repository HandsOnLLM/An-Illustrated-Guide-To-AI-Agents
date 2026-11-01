using System.ComponentModel;

namespace IllustratedAgents;

/// <summary>One sub-task in a plan.</summary>
public sealed class PlanItem
{
    public PlanItem(string task) => Task = task;

    public string Task { get; }
    public bool Done { get; set; }
}

/// <summary>
/// A ReAct planner that gives the model two tools to keep its own plan: <c>update_plan</c> and
/// <c>mark_done</c>. Chapter 6.
/// </summary>
public class PlanAndSolve : ReAct
{
    public PlanAndSolve(Tools tools, int maxSteps = 10) : base(maxSteps)
    {
        tools.AddTool(
            "update_plan",
            UpdatePlan,
            "Create or overwrite the plan with a list of sub-tasks: update_plan(items: list[str])");
        tools.AddTool(
            "mark_done",
            MarkDone,
            "Mark a sub-task complete by 1-based index: mark_done(index: int)");
    }

    public List<PlanItem> Plan { get; private set; } = [];

    public override string Prompt
    {
        get
        {
            return base.Prompt + """

                ## Planning

                For non-trivial tasks, call `update_plan` first to outline your approach, then `mark_done` as you complete each sub-task. Revise the plan with `update_plan` whenever new information changes what is needed.

                """;
        }
    }

    /// <summary>Replace the plan with new sub-tasks, none of them done.</summary>
    [Description("Create or overwrite the plan with a list of sub-tasks.")]
    public string UpdatePlan(List<string> items)
    {
        Plan = items.Select(item => new PlanItem(item)).ToList();
        return $"Plan updated:\n{Render()}";
    }

    /// <summary>Mark a sub-task done, counting from 1.</summary>
    [Description("Mark a sub-task complete by 1-based index.")]
    public string MarkDone(int index)
    {
        if (index < 1 || index > Plan.Count)
        {
            return $"There is no sub-task {index}. The plan has {Plan.Count}.";
        }
        Plan[index - 1].Done = true;
        return $"Plan:\n{Render()}";
    }

    /// <summary>The plan as a checklist: <c>[x] 1. Task</c> or <c>[ ] 2. Task</c>, one per line.</summary>
    public string Render()
    {
        return string.Join("\n", Plan.Select((item, i) => $"{(item.Done ? "[x]" : "[ ]")} {i + 1}. {item.Task}"));
    }
}
