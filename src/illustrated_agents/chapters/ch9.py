from illustrated_agents.chapters import ch5_native, ch6_skills
from illustrated_agents.chapters.ch2 import Response
from illustrated_agents.chapters.ch5_native import Tools, LLM, Memory
from illustrated_agents.chapters.ch6 import ReAct
from illustrated_agents.chapters.ch6_skills import Skills
from illustrated_agents.utils import DiffViewer, ChapterOverview


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


class Memory:
    """Simple memory module to store conversation history."""

    def __init__(self):
        self.messages = []

    def add(self, role: str, content: str, tool_call: dict = None, image_data: str = None):
        """Add a message to memory."""
        # Image
        if image_data:
            content = [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}},
                {"type": "text", "text": content},
            ]
        # Main message
        message = {"role": role, "content": content}

        # Tool call
        if tool_call:
            message["tool_calls"] = [tool_call]

        # Append message to memory
        self.messages.append(message)

    def get_messages(self) -> list[dict]:
        """Get all messages."""
        return self.messages


what_we_built = ChapterOverview(
    [
        ("agent.py", "updated", "Added the `image_url` parameter to process images."),
        ("llm.py", None, ""),
        ("memory.py", "updated", "Track images in the conversation history."),
        ("reflection.py", None, ""),
        ("planning.py", None, ""),
        ("skills.py", None, ""),
        ("toolbox.py", None, ""),
        ("tools.py", None, ""),
    ]
)


tinyagents_diff = DiffViewer(ch6_skills.TinyAgent, TinyAgent, "ch6_skills.TinyAgent", "ch9.TinyAgent")
memory_diff = DiffViewer(ch5_native.Memory, Memory, "ch5_native.Memory", "ch9.Memory")


what_we_built = ChapterOverview(
    [
        ("agent.py", "updated", "Allow the agent to process images in addition to text."),
        ("llm.py", None, ""),
        ("memory.py", "updated", "Track images in the conversation history for the Agent to access."),
        ("planning.py", None, ""),
        ("skills.py", None, ""),
        ("toolbox.py", None, ""),
        ("tools.py", None, ""),
    ]
)
