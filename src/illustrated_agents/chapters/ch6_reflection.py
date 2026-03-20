from illustrated_agents import LLM, Memory, Tools, ReAct, Reflector
from illustrated_agents.utils import DiffViewer, CodeAnnotator, ChapterOverview
from illustrated_agents.chapters import ch6


class TinyAgent:
    """A minimal, modular, and educational agent framework."""

    def __init__(self, llm: LLM, memory: Memory, tools: Tools, planner: ReAct, reflector: Reflector):
        self.llm = llm
        self.memory = memory
        self.tools = tools
        self.planner = planner
        self.reflector = reflector
        self.skills = None  # Chapter 6: Add Skills

        # Build system prompt with all components
        system_prompt = "You are a helpful AI agent.\n\n"
        system_prompt += self.planner.prompt + "\n\n"
        system_prompt += self.tools.prompt
        self.memory.add("user", system_prompt)

    def run(self, task: str) -> str:
        """Run the agent on a task."""
        self.memory.add("user", task)

        # `Autonomy` loop
        for step in range(self.planner.max_steps):
            # Reflection step before taking the next action
            if self.reflector.should_reflect(step):
                self.memory.add("user", self.reflector.prompt)

            # Perform a step and check for completion
            result = self._step()
            if result is not None:
                return result

        return "Max steps reached without completion."

    def _step(self) -> str | None:
        """Perform a single step."""
        # Generate response and add to memory
        response = self.llm.generate(self.memory.get_messages())
        self.memory.add("assistant", response)

        # Parse planner's response to extract action if needed
        response = self.planner.parse(response)

        # Tool parsing and execution
        if self.tools.has_tool_call(response):
            return self._execute_action(response)

        return None

    def _execute_action(self, action: str) -> str | None:
        """Execute a tool action."""
        tool_call = self.tools.parse_tool_call(action)

        # Final answer ends the loop
        if tool_call["tool"] == "final_answer":
            return tool_call.get("kwargs", "")

        # Execute tool and extract the observation
        observation = self.tools.run_tool(tool_call)
        obs_prompt = f"OBSERVATION: {action} -> {observation}"
        self.memory.add("user", obs_prompt)

        return None


what_we_built = ChapterOverview(
    [
        ("agent.py", "updated", "During the `for-loop`, check if reflection needs to be activated."),
        ("llm.py", None, ""),
        ("memory.py", None, ""),
        ("planning.py", None, ""),
        ("reflection.py", "new", "Added `Reflection` to reflect its work every n steps."),
        ("toolbox.py", None, ""),
        ("tools.py", None, ""),
    ]
)


tinyagents_diff = DiffViewer(ch6.TinyAgent, TinyAgent, "ch6.TinyAgent without Reflection", "ch6.TinyAgent Reflection")


reflector_annotated = CodeAnnotator(
    Reflector,
    annotations={
        10: "The interval parameter defines how often the agent reflects on its actions. We could set it every single step, but that might fill up the context window and Memory too quickly.",
        (16, 21): """
        The reflection prompt is straightforward and encourages the agent to self-evaluate its progress and consider alternative approaches. 
        This can help the agent avoid getting stuck in unproductive loops.
        """,
    },
)
