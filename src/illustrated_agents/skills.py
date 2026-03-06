from pathlib import Path

import yaml


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

    def load_from_file(self, path: str):
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

You have specialized skills available. To use a skill, call it like a tool but without any arguments except the skill name, for example:
{{"tool": "use_skill", "kwargs": {{"name": "skill_name"}}}}

The skill will provide detailed instructions for completing the task.

Available skills:
{self.descriptions}
"""

    @property
    def descriptions(self) -> str:
        """Get short descriptions of all skills."""
        return "\n".join(f"- `{name}`: {skill['description']}" for name, skill in self.skills.items())
