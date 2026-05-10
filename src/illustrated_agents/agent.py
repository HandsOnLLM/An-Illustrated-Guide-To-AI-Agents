from illustrated_agents.llm import LLM, Response
from illustrated_agents.memory import Memory
from illustrated_agents.planning import ReAct
from illustrated_agents.tools import Tools
from illustrated_agents.display import Display


class TinyAgent:
    """A minimal, modular, and educational agent framework."""

    def __init__(self, llm: LLM, memory: Memory, tools: Tools, planner: ReAct, display=Display):
        self.llm = llm
        self.memory = memory
        self.tools = tools
        self.planner = planner
        self.display = display

        # Build system prompt with all components
        system_prompt = "You are a helpful AI agent.\n\n"
        system_prompt += self.planner.prompt + "\n\n"
        system_prompt += self.tools.prompt
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
        # THOUGHT: generate reasoning and potential action
        self.display("thinking")
        response = self.llm.generate(self.memory.get_messages(), tools=self.tools.schemas)
        self.memory.add("assistant", response.content, tool_call=response.tool_call)
        self.display("response", response)

        # Parse planner's response to extract action if needed
        response = self.planner.parse(response)

        # Tool parsing
        response = self.tools.parse(response)

        # Stopping mechanism
        if self.tools.is_done(response):
            return response.content

        return self._execute_action(response)

    def _execute_action(self, response: Response) -> None:
        """Execute a tool action."""
        # ACTION: execute tools
        self.display("tool_call", response)
        result = self.tools.execute(response)

        # OBSERVATION: add tool results to memory and display
        role, observation = self.tools.observation(result)
        self.memory.add(role, observation)
        self.display("observation", observation)

        return None
