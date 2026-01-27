from .llm import LLM
from .memory import Memory
from .planning import ReAct
from .tools import Tools
from .reflection import Reflector


class TinyAgent:
    def __init__(
        self,
        llm: LLM,
        memory: Memory,
        tools: Tools,
        planner: ReAct,
        reflector: Reflector = None,
        max_steps: int = 10,
    ):
        """A simple agent that responds to user inputs.

        Arguments:
            llm: The LLM to use for generating responses.
            memory: Memory module to store conversation history.
            tools: A list of tools the agent can use.
            planner: Allows for planning with ReAct framework.
            reflector: Optional reflector for self-evaluation.
            max_steps: Maximum number of steps before stopping.
        """
        self.llm = llm
        self.memory = memory
        self.tools = tools
        self.planner = planner
        self.max_steps = max_steps
        self.reflector = reflector

        # Initialize memory with system prompt and tool descriptions
        system_prompt = (
            "You are a helpful AI agent.\n\n"
            + self.planner.system_prompt
            + "\n\n"
            + self.tools.prompt
        )
        self.memory.add("user", system_prompt)

    def run(self, task: str) -> str:
        """Run the agent on a given task."""
        self.memory.add("user", task)

        for step in range(self.max_steps):
            # # Reflection step
            # if self.reflector and self.reflector.should_reflect(step):
            #     self.memory.add("user", self.reflector.prompt)

            result = self._step()
            if result is not None:
                return result

        return "Max steps reached without completion."

    def _step(self) -> str | None:
        """Perform a single step of the agent's reasoning process."""
        # Generate response
        output = self.llm.generate(self.memory.get_messages())
        self.memory.add("assistant", output)
        print("OUTPUT", output)

        # Parse ReAct response
        parsed = self.planner.parse_react(output)
        print("PARSED", parsed)

        # Execute action if present
        if self.tools.is_tool_call(parsed["ACTION"]):
            return self._execute_action(parsed["ACTION"])

        return None

    def _execute_action(self, action: str) -> str | None:
        """Execute a tool action.

        Returns the final answer string if complete, None to continue.
        """
        # Parse the tool call
        tool_call = self.tools.parse_tool_call(action)
        print("TOOL:", tool_call)

        # Final answer ends the loop
        if tool_call["tool"] == "final_answer":
            return tool_call.get("args", "")

        # Execute tool and add observation to memory
        observation = self.tools.run_tool(tool_call)
        obs_prompt = self.planner.format_observation(action, observation)
        self.memory.add("user", obs_prompt)

        return None
