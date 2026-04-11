import yaml
from pathlib import Path

from illustrated_agents.utils import DiffViewer, CodeAnnotator, ChapterOverview
from illustrated_agents.chapters import ch6_native
from illustrated_agents.chapters.ch6_native import LLM, Memory, Tools, ReAct, Response


class Skills:
    """Skill loader for the Agent.

    Skills are recipes that teach the agent what to do, when to do it, and how.
    They are defined in SKILL.md files with YAML frontmatter (name, description)
    and markdown instructions.

    The skills are loaded progressively. As such, the name and description are
    available in the system prompt, but the full instructions are only injected
    when the agent **activates** a skill.
    """

    def __init__(self):
        self.skills = {}

    def add_skill(self, path: str):
        """Load a skill from a SKILL.md file"""
        content = Path(path).read_text(encoding="utf-8")

        # Split on YAML delimiters and extract the frontmatter and body
        parts = content.split("---", 2)

        # Frontmatter
        frontmatter = yaml.safe_load(parts[1])
        name = frontmatter["name"]
        description = frontmatter["description"]

        # Body
        body = parts[2].strip()

        # Store the skill
        self.skills[name] = {
            "description": description,
            "instructions": body,
        }

    def activate(self, tool_call: dict) -> str:
        """Activate a skill and return formatted observation.

        Arguments:
            tool_call: A parsed tool call dict with "tool" and "kwargs" keys.

        Returns:
            Formatted observation with skill instructions.
        """
        name = tool_call["kwargs"]["name"]
        if name in self.skills:
            instructions = self.skills[name]["instructions"]
            return f"Skill '{name}' activated. Follow these instructions:\n\n{instructions}"
        return f"Skill '{name}' not found. Available skills: {', '.join(self.skills.keys())}"

    @property
    def prompt(self) -> str:
        """Generate prompt with skill descriptions (not full instructions)."""
        return f"""
# Skills

You have specialized skills available. To use a skill,
call it like a tool by referencing their name.

The skill will provide detailed instructions for completing the task.

Available skills:
{self.descriptions}
"""

    @property
    def descriptions(self) -> str:
        """Get short descriptions of all skills."""
        return "\n".join(f"- `{name}`: {skill['description']}" for name, skill in self.skills.items())

    def as_tool(self, name: str):
        """Convert a skill's instruction to a function so it can be called as a tool."""

        def skill_as_a_tool():
            return self.skills[name]["instructions"]

        skill_as_a_tool.__name__ = name
        return skill_as_a_tool


class TinyAgent:
    """A minimal, modular, and educational agent framework."""

    def __init__(self, llm: LLM, memory: Memory, tools: Tools, planner: ReAct, skills: Skills):
        self.llm = llm
        self.memory = memory
        self.tools = tools
        self.planner = planner
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
            result = self._step()
            if result is not None:
                return result

        return "Max steps reached without completion."

    def _step(self) -> str | None:
        """Perform a single step."""
        # Generate response and add to memory
        response = self.llm.generate(self.memory.get_messages(), tools=self.tools.schemas)
        self.memory.add("assistant", response.content, tool_call=response.tool_call)

        # Parse planner's response to extract action if needed
        response = self.planner.parse(response)

        # Tool parsing and execution
        if self.tools.has_tool_call(response):
            return self._execute_action(response)

        # Stopping mechanism for native tool calling
        if not response.tool_call:
            return response.content

        return None

    def _execute_action(self, response: Response) -> str | None:
        """Execute a tool action."""
        tool_call = self.tools.parse_tool_call(response)

        # Final answer ends the loop
        if tool_call["tool"] == "final_answer":
            return tool_call.get("kwargs", "")

        # Execute tool and extract the observation
        observation = self.tools.run_tool(tool_call)

        # Native tool calling should get the role `tool`
        if self.tools.schemas:
            self.memory.add("tool", str(observation))
        else:
            self.memory.add("user", f"OBSERVATION: {observation}")

        return None


what_we_built = ChapterOverview(
    [
        ("agent.py", "updated", "Added instructions in the system prompt for skill activation."),
        ("llm.py", None, ""),
        ("memory.py", None, ""),
        ("planning.py", None, ""),
        ("skills.py", "new", "Added `Skills` class for loading and activating skills as tools."),
        ("toolbox.py", None, ""),
        ("tools.py", None, ""),
    ]
)


tinyagents_diff = DiffViewer(ch6_native.TinyAgent, TinyAgent, "ch6_native.TinyAgent", "ch6_skills.TinyAgent")


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
    Skills.add_skill,
    annotations={
        6: "The two parts (yaml frontmatter and markdown body) are extracted from the SKILL.md file.",
        (
            9,
            11,
        ): "The frontmatter is separately parsed to get name and description. Note that it can contain other metadata as well.",
        14: "The instructions (body) are stored separately.",
        (
            17,
            20,
        ): "The skill is stored in the skills dictionary where the description and instructions can be accessed separately.",
    },
)

skills_as_tool_annotated = CodeAnnotator(
    Skills.as_tool,
    annotations={
        (
            4,
            5,
        ): "A dynamic function is created to return the skill instructions. This allows the skill to be called as a tool.",
        7: "The function name is set to the skill name so the correct name is used when calling the skill.",
    },
)
