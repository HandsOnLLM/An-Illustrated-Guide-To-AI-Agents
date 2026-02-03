"""Example: Using Skills with TinyAgent."""

import json
from pathlib import Path

import illustrated_agents
from illustrated_agents import LLM, Memory, ReAct, Skills, Reflector, MCPTools
from illustrated_agents.chapters.ch6_skills import TinyAgent


if __name__ == "__main__":
    # Create LLM
    llm = LLM(model="ollama/gemma3:12b")

    # Create MCP-based tools (includes read_markdown)
    tools = MCPTools()

    # Load skills
    skills = Skills()
    file_analyzer_path = Path(illustrated_agents.__file__).parent / "skills" / "file_analyzer" / "SKILL.md"
    skills.load_from_file(file_analyzer_path)

    # Show what's loaded
    print("=== Loaded Skills ===")
    print(skills.descriptions)
    print()

    # Create agent with skills
    memory = Memory()
    planner = ReAct()
    reflector = Reflector()
    agent = TinyAgent(llm=llm, tools=tools, memory=memory, planner=planner, reflector=reflector, skills=skills)

    # Run a task that will trigger the skill
    query = "Analyze and summarize the file at https://raw.githubusercontent.com/MaartenGr/BERTopic/refs/heads/master/README.md"
    response = agent.run(query)
    print("==== QUERY ====\n", query, "\n")
    print("==== RESPONSE ====\n", response)

    # Show messages in memory
    print("\n\n\n==== Messages in Memory ====")
    print(json.dumps(agent.memory.get_messages(), indent=4))
