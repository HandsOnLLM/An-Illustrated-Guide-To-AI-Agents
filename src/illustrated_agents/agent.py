from illustrated_agents.llm import LLM, Response
from illustrated_agents.memory import Memory
from illustrated_agents.planning import ReAct
from illustrated_agents.tools import Tools
from illustrated_agents.skills import Skills
from illustrated_agents.display import Display


class TinyAgent:
    """A minimal, modular, and educational agent framework."""

    def __init__(
        self, llm: LLM, memory: Memory, tools: Tools, planner: ReAct, skills: Skills, display=Display
    ):
        self.llm = llm
        self.memory = memory
        self.tools = tools
        self.planner = planner
        self.skills = skills
        self.display = display

        # Build system prompt with all components
        system_prompt = "You are a helpful AI agent.\n\n"
        system_prompt += self.planner.prompt + "\n\n"
        system_prompt += self.tools.prompt
        system_prompt += self.skills.prompt
        self.memory.add("system", system_prompt)

    def run(self, task: str, image_data: str = None) -> str:
        """Run the agent on a task."""
        self.memory.add("user", task, image_data=image_data)

        # `Autonomy` loop
        for step in range(self.planner.max_steps):
            result = self._step()
            if result is not None:
                return result

        return "Max steps reached without completion."

    def _step(self) -> str | None:
        """Perform a single step."""
        # Generate response and add to memory
        self.display("thinking")
        response = self.llm.generate(self.memory.get_messages(), tools=self.tools.schemas)
        self.memory.add("assistant", response.content, tool_call=response.tool_call)
        self.display("response", response)

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
        self.display("tool_call", response)

        # Final answer ends the loop
        if tool_call["tool"] == "final_answer":
            return tool_call.get("kwargs", "")

        # Execute tool and extract the observation
        observation = self.tools.run_tool(tool_call)

        # Native tool calling should get the role `tool`
        self.display("observation", observation)
        if self.tools.schemas:
            self.memory.add("tool", str(observation))
        else:
            self.memory.add("user", f"OBSERVATION: {observation}")

        return None
