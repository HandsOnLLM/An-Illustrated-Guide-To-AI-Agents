from illustrated_agents.llm import LLM
from illustrated_agents.memory import Memory
from illustrated_agents.planning import ReAct
from illustrated_agents.tools import Tools
from illustrated_agents.reflection import Reflector
from illustrated_agents.skills import Skills


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
