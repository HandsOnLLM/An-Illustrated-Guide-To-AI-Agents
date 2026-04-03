from illustrated_agents import LLM, Memory, Tools, ReAct
from illustrated_agents.skills import Skills
from illustrated_agents.reflection import Reflector
from illustrated_agents.utils import DiffViewer, CodeAnnotator, ChapterOverview
from illustrated_agents.chapters import ch6_reflection


class TinyAgent:
    """A minimal, modular, and educational agent framework."""

    def __init__(self, llm: LLM, memory: Memory, tools: Tools, planner: ReAct, reflector: Reflector, skills: Skills):
        self.llm = llm
        self.memory = memory
        self.tools = tools
        self.planner = planner
        self.reflector = reflector
        self.skills = skills

        # Build system prompt with all components
        system_prompt = "You are a helpful AI agent.\n\n"
        system_prompt += self.planner.prompt + "\n\n"
        system_prompt += self.tools.prompt
        system_prompt += self.skills.prompt
        self.memory.add("system", system_prompt)

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

        # Activate skill and extract the observation
        if tool_call["tool"] == "use_skill":
            observation = self.skills.activate(tool_call)

        # Execute tool and extract the observation
        else:
            observation = self.tools.run_tool(tool_call)

        # Format the observation and add it to memory
        obs_prompt = f"OBSERVATION: {action} -> {observation}"
        self.memory.add("user", obs_prompt)

        return None


what_we_built = ChapterOverview(
    [
        ("agent.py", "updated", "Added instructions in the system prompt for skill activiation."),
        ("llm.py", None, ""),
        ("memory.py", None, ""),
        ("planning.py", None, ""),
        ("reflection.py", None, ""),
        ("skills.py", "new", "Instruction-based skills"),
        ("toolbox.py", None, ""),
        ("tools.py", None, ""),
    ]
)


tinyagents_diff = DiffViewer(ch6_reflection.TinyAgent, TinyAgent, "ch6_reflection.TinyAgent", "ch6_skills.TinyAgent")


skills_class_annotated = CodeAnnotator(
    Skills.prompt,
    annotations={
        5: "Separate section for skill descriptions in the system prompt.",
        (
            7,
            8,
        ): "Method to activate a skill and retrieve its instructions. The same structure as a tool call is used. Everything is a tool!",
        13: "Only descriptions go into the prompt - instructions are loaded on demand.",
    },
)

skills_activate_annotated = CodeAnnotator(
    Skills.activate,
    annotations={
        10: "The skill is activated as if it was a tool call.",
        13: "An 'observation' is returned with the skill instructions.",
    },
)

skills_load_annotated = CodeAnnotator(
    Skills.load_from_file,
    annotations={
        6: "The two parts (yaml frontmatter and markdown body) are extracted from the SKILL.md file.",
        (9, 11): "The frontmatter is separately parsed to get name and description. Note that it can contain other metadata as well.",
        14: "The instructions (body) are stored separately.",
        (17, 20): "The skill is stored in the skills dictionary where the description and instructions can be accessed separately.",
    },
)
