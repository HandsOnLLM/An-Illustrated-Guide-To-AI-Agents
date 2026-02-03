import json

from illustrated_agents import LLM, Tools, Memory, Reflector, ReAct
from illustrated_agents.chapters.ch6_reflection import TinyAgent


if __name__ == "__main__":
    # Define tools
    def calculator(a: str, b: str) -> float:
        return float(a) + float(b)

    def get_weather(location: str) -> str:
        return f"Weather in {location}: Sunny, 72°F"

    # Register tools
    tools = Tools()
    tools.add_tool("calculator", calculator, "Adds two numbers: calculator(a, b)")
    tools.add_tool("get_weather", get_weather, "Gets weather: get_weather(city)")

    # LLM
    llm = LLM(model="ollama/gemma3:12b")

    # Memory
    memory = Memory()

    # ReAct
    react = ReAct(max_steps=10)

    # Reflector
    reflector = Reflector(interval=3)

    # Create agent
    agent = TinyAgent(llm=llm, tools=tools, memory=memory, planner=react, reflector=reflector)

    # Multi-step task with reasoning
    query = """
I'm planning a trip! Help me with these tasks:
1. What's the weather in New York City?
2. What's the weather in Los Angeles?
3. I saved $150.50 and my friend is giving me $75.25. How much do I have for the trip?

Based on the weather, which city would you recommend I visit?
"""
    output = agent.run(query)
    print("==== QUERY ====\n", query, "\n")
    print("==== RESPONSE ====\n", output)

    # Show messages in memory
    print("\n\n\n==== Messages in Memory ====")
    print(json.dumps(agent.memory.get_messages(), indent=4))
