from illustrated_agents import LLM, Memory, Tools, ReAct, Reflector, Skills
from illustrated_agents.utils import DiffViewer
from illustrated_agents.chapters import ch4, ch6_skills


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
        self.memory.add("user", system_prompt)

    def run(self, task: str, image_url: str = None) -> str:
        """Run the agent on a task."""
        self.memory.add("user", task, image_url=image_url)

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
            return tool_call.get("args", "")

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


class Memory:
    """Simple memory module to store conversation history."""

    def __init__(self):
        self.messages = []

    def add(self, role: str, content: str, image_url: str = None):
        """Add a message to memory."""
        if image_url:
            content = [{"type": "text", "text": content}, {"type": "image_url", "image_url": {"url": image_url}}]
        self.messages.append({"role": role, "content": content})

    def get_messages(self) -> list[dict]:
        """Get all messages."""
        return self.messages


tinyagents_diff = DiffViewer(ch6_skills.TinyAgent, TinyAgent, "ch6.TinyAgent", "ch9.TinyAgent")
memory_diff = DiffViewer(ch4.Memory, Memory, "ch4.Memory", "ch9.Memory")
