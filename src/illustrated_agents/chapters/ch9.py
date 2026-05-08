from illustrated_agents.chapters import ch4, ch6_skills
from illustrated_agents.chapters.ch2 import LLM, Response, Trajectory
from illustrated_agents.chapters.ch4 import Memory
from illustrated_agents.chapters.ch5 import Tools
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

        self.trajectory = Trajectory()

        # Build system prompt with all components
        system_prompt = "You are a helpful assistant.\n"
        system_prompt += self.planner.prompt + "\n"
        system_prompt += self.tools.prompt + "\n"
        system_prompt += self.skills.prompt + "\n"
        self.memory.add("system", system_prompt)

    def run(self, task: str, image_data: str = None) -> str:
        """Run the agent on a task."""
        self.memory.add("user", task, image_data=image_data)
        self.trajectory.initialize(task)

        # `Autonomy` loop
        for step in range(self.planner.max_steps):
            result = self._step()
            if result is not None:
                return result

        return "Max steps reached without completion."

    def _step(self) -> str:
        """Perform a single step."""
        # THOUGHT: Generate response and add to memory
        response = self.llm.generate(self.memory.get_messages(), tools=self.tools.schemas)
        self.memory.add("assistant", response.content, tool_call=response.tool_call)

        # Tool parsing
        response = self.tools.parse(response)

        # ANSWER: Stopping mechanism
        if self.tools.is_done(response):
            self.trajectory.add(response)
            return response.content

        return self._execute_action(response)

    def _execute_action(self, response: Response) -> None:
        """Execute a tool action."""

        # ACTION: execute tools
        result = self.tools.execute(response)

        # OBSERVATION: add tool results to memory and display
        role, observation = self.tools.observation(result)
        self.memory.add(role, observation)
        self.trajectory.add(response, observation)

        return None


class MultimodalMemory(Memory):
    """Simple memory module to store conversation history."""

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


tinyagents_diff = DiffViewer(ch6_skills.TinyAgent, TinyAgent, "ch6_skills.TinyAgent", "ch9.TinyAgent")
memory_diff = DiffViewer(ch4.Memory, MultimodalMemory, "ch4.Memory", "ch9.MultimodalMemory")


what_we_built = ChapterOverview(
    [
        ("agent.py", "updated", "Allow the agent to process images in addition to text."),
        ("llm.py", None, ""),
        ("memory.py", "updated", "Track images in the conversation history for the Agent to access."),
        ("planning.py", None, ""),
        ("skills.py", None, ""),
        ("toolbox.py", None, ""),
        ("tools.py", None, ""),
        ("trajectory.py", None, ""),
    ]
)
