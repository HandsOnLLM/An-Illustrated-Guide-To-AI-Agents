# `TinyAgent`

The source code for "An Illustrated Guide to AI Agents" where you build an `TinyAgent` from scratch by building it up with one module at a time:

![../../images/tinyagents.png](../../images/tinyagents.png)

The general idea is that each module is self-contained and added to the `TinyAgent` with minimal changes when progressing through the book. At the end, you will have learned about each module in detail and can **Build an Agent from Scratch** like so:


```python
# Modules to augment your Agent
from illustrated_agents.llm import LLM  # llm.py
from illustrated_agents.memory import Memory  # memory.py
from illustrated_agents.tools import MCPTools  # tools.py
from illustrated_agents.planning import ReAct  # planning.py
from illustrated_agents.reflection import Reflector  # reflection.py
from illustrated_agents.skills import Skills  # skills.py

# The TinyAgent
from illustrated_agents.agent import TinyAgent  # tinyagent.py

# Choose an LLM
llm = LLM(model="ollama/gemma3:12b")

# Add Memory (simple conversation memory)
memory = Memory()

# Add Tools through a local MCP Server and Client
tools = MCPTools()

# Create autonomous behavior through THOUGHT/ACTION/OBSERVATION cycles
react = ReAct(max_steps=10)

# Reflect on current situation every 5 steps
reflector = Reflector(interval=5)

# Add SKILL.md
skills = Skills()
skills.load_from_file(path_to_my_skill)

# Create agent
agent = TinyAgent(
    llm=llm, 
    tools=tools, 
    memory=memory, 
    planner=react, 
    reflector=reflector, 
    skills=skills
)
```

Each module is separated from the `TinyAgent` so that it can be learned as a modular component step-by-step.