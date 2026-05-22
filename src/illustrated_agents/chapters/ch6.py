import re
from illustrated_agents.chapters import ch5
from illustrated_agents.chapters.ch2 import LLM, Response, Trajectory
from illustrated_agents.chapters.ch4 import Memory
from illustrated_agents.chapters.ch5 import Tools
from illustrated_agents.utils import DiffViewer, CodeAnnotator, ChapterOverview


class ReAct:
    """ReAct module."""

    def __init__(self, max_steps: int = 10):
        """Initialize ReAct module.

        Arguments:
            max_steps: Maximum number of ReAct steps to perform.
        """
        self.max_steps = max_steps

    @property
    def prompt(self) -> str:
        return """
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

"""

    def parse(self, response: Response) -> Response:
        """Parse a ReAct formatted response into THOUGHT and ACTION."""
        text = response.content

        # The patterns for each section
        patterns = {
            "THOUGHT": r"THOUGHT:\s*(.+?)(?=ACTION:|OBSERVATION:|$)",
            "ACTION": r"ACTION:\s*(.+?)(?=THOUGHT:|OBSERVATION:|$)",
        }

        # Extract each section using regex
        result = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.DOTALL)
            result[key] = match.group(1).strip() if match else ""

        # Update Response and extract only the action
        response.content = result["ACTION"]
        response.reasoning = result["THOUGHT"]
        return response


class NativeReAct(ReAct):
    """ReAct using native LLM reasoning instead of text-based parsing."""

    @property
    def prompt(self) -> str:
        return ""

    def parse(self, response: Response) -> Response:
        return response


class PlanAndSolve(ReAct):
    """ReAct planner that gives the LLM tools to create and update its own plan."""

    def __init__(self, tools: Tools, max_steps: int = 10):
        """Initialize PlanAndSolve planner.

        Arguments:
            tools: The tool registry to attach `update_plan` and `mark_done` to.
            max_steps: Maximum number of ReAct steps to perform.
        """
        super().__init__(max_steps)
        self.plan: list[dict] = []

        tools.add_tool(
            "update_plan",
            self.update_plan,
            "Create or overwrite the plan with a list of sub-tasks: update_plan(items: list[str])",
        )
        tools.add_tool(
            "mark_done",
            self.mark_done,
            "Mark a sub-task complete by 1-based index: mark_done(index: int)",
        )

    @property
    def prompt(self) -> str:
        return super().prompt + (
            "\n## Planning\n\n"
            "For non-trivial tasks, call `update_plan` first to outline your approach, "
            "then `mark_done` as you complete each sub-task. Revise the plan with "
            "`update_plan` whenever new information changes what is needed.\n"
        )

    def update_plan(self, items: list[str]) -> str:
        """Replace the plan with a new list of sub-tasks."""
        self.plan = [{"task": item, "done": False} for item in items]
        return f"Plan updated:\n{self._render()}"

    def mark_done(self, index: int) -> str:
        """Mark a sub-task complete by 1-based index."""
        self.plan[index - 1]["done"] = True
        return f"Plan:\n{self._render()}"

    def _render(self) -> str:
        return "\n".join(
            f"{'[x]' if item['done'] else '[ ]'} {i + 1}. {item['task']}"
            for i, item in enumerate(self.plan)
        )


class Reflexion:
    """Reflector that periodically critiques recent steps and injects a course correction."""

    def __init__(self, llm: LLM, interval: int = 3):
        """Initialize Reflexion reflector.

        Arguments:
            llm: The LLM used to generate critiques.
            interval: Reflect every `interval` steps.
        """
        self.llm = llm
        self.interval = interval

    def reflect(self, memory: Memory, step: int) -> None:
        """Critique recent steps and add a corrective user message to memory."""
        if step == 0 or step % self.interval:
            return
        critique = self.llm.generate(
            [
                {
                    "role": "system",
                    "content": "Critique the agent's recent steps and suggest a course correction.",
                },
                *memory.get_messages()[-6:],
            ]
        )
        memory.add("user", f"[Reflection] {critique.content}")


class TinyAgent:
    """A minimal, modular, and educational agent framework."""

    def __init__(self, llm: LLM, memory: Memory, tools: Tools, planner: ReAct):
        self.llm = llm
        self.memory = memory
        self.tools = tools
        self.planner = planner

        self.trajectory = Trajectory()

        # Build system prompt with all components
        system_prompt = "You are a helpful assistant.\n\n"
        system_prompt += self.planner.prompt
        system_prompt += self.tools.prompt
        self.memory.add("system", system_prompt)

    def run(self, task: str) -> str:
        """Run the agent on a task."""
        self.memory.add("user", task)
        self.trajectory.initialize(task)

        # *Autonomy* loop
        for step in range(self.planner.max_steps):
            result = self._step()
            if result is not None:
                return result

        return "Max steps reached without completion."

    def _step(self) -> str | None:
        """Perform a single step."""
        # THOUGHT: Generate response and add to memory
        response = self.llm.generate(
            self.memory.get_messages(), tools=self.tools.schemas
        )
        self.memory.add(
            "assistant", response.content, tool_call=response.tool_call
        )

        # Tool parsing
        response = self.planner.parse(response)
        response = self.tools.parse(response)

        # ANSWER: Stopping mechanism
        if self.tools.is_done(response):
            self.trajectory.add(response)
            return response.content

        return self._execute_action(response)

    def _execute_action(self, response: Response) -> None:
        """Execute a tool action."""

        # ACTION: execute tools
        result = self.tools.execute(response)

        # OBSERVATION: add tool results to memory and display
        role, observation = self.tools.observation(result)
        self.memory.add(role, observation)
        self.trajectory.add(response, observation)

        return None


what_we_built_native = ChapterOverview(
    [
        ("agent.py", None, ""),
        ("llm.py", None, ""),
        ("memory.py", None, ""),
        ("planning.py", "new", "Added the `NativeReAct` class"),
        ("toolbox.py", None, ""),
        ("tools.py", None, ""),
        ("trajectory.py", None, ""),
    ]
)


what_we_built = ChapterOverview(
    [
        ("agent.py", "updated", "Autonomy with a for-loop and ReAct planner."),
        ("llm.py", None, ""),
        ("memory.py", None, ""),
        ("planning.py", "new", "Added the ReAct (Reason and Act) framework"),
        ("toolbox.py", None, ""),
        ("tools.py", None, ""),
        ("trajectory.py", None, ""),
    ]
)


tinyagents_diff = DiffViewer(
    ch5.TinyAgent, TinyAgent, "ch5.TinyAgent", "ch6.TinyAgent"
)


react_prompt_annotated = CodeAnnotator(
    ReAct.prompt,
    annotations={
        (6, 7): "Main explanation of the ReAct framework.",
        12: "<b>THOUGHT</b> - reasoning about next step.",
        (13, 18): "<b>ACTION</b> - tool call format.",
        19: "<b>OBSERVATION</b> - provided after action.",
        (
            26,
            30,
        ): "<b>ACTION</b> - Final answer format - must be used to complete the task.",
    },
)


react_parse_annotated = CodeAnnotator(
    ReAct.parse,
    annotations={
        (
            6,
            9,
        ): """Extracts the <b>THOUGHT</b> and <b>ACTION</b> sections from the response. 
        Note that we stop at <b>OBSERVATION</b> to avoid hallucinated observations.""",
        (14, 15): """Searches for all matches using regular expressions (regex). 
        The re.DOTALL flag allows . to match newlines and re.IGNORECASE makes the search case-insensitive. 
        If a match is found, it extracts and trims the content; otherwise, it assigns an empty string.""",
    },
)

tinyagent_init_annotated = CodeAnnotator(
    TinyAgent.__init__,
    annotations={
        (
            11,
            12,
        ): "We added the prompt of the ReAct module to the system prompt and follow it up with the tools prompt.",
    },
)

tinyagent_run_annotated = CodeAnnotator(
    TinyAgent.run,
    annotations={
        3: "The initial task is immediately added to memory as a user message so that the Agent can reference it during the loop.",
        (
            7,
            8,
        ): "The `Autonomy` (ReAct) loop where the agent performs steps until completion or max steps reached.",
    },
)

tinyagent_step_annotated = CodeAnnotator(
    TinyAgent._step,
    annotations={
        (4, 5): "A response is generated and added to memory and trajectory.",
        8: "The output needs to be parsed into THOUGHT and ACTION using the ReAct parser.",
        (
            12,
            14,
        ): "We check if the `Response` contains a tool call that signals completion (final_answer). If so, we return the final answer and end the loop. The step is also saved to the trajectory.",
        16: "If the `Response` contains a tool call, execute it.",
    },
)

tinyagent_action_annotated = CodeAnnotator(
    TinyAgent._execute_action,
    annotations={
        5: "The tool call is executed using the `Tools` class which looks up the tool in the registry and calls it.",
        (
            8,
            9,
        ): "The result of the tool execution is stored as an observation in memory. This way, the LLM can reference the observation in the next step.",
        10: "The step is also saved to the trajectory with the observation.",
    },
)
