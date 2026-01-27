import json
from illustrated_agents import LLM, Memory, Tools
from illustrated_agents.chapters.ch5 import TinyAgent


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

    # Create agent
    llm = LLM(model="ollama/gemma3:12b")
    memory = Memory()
    agent = TinyAgent(llm=llm, tools=tools, memory=memory)

    # Single tool call
    query = "What is 5.1281 plus 7.323?"
    output = agent.run(query)
    print("==== QUERY ====\n", query, "\n")
    print("==== RESPONSE ====\n", output)

    # Show messages in memory
    print("\n\n\n==== Messages in Memory ====")
    print(json.dumps(agent.memory.get_messages(), indent=4))
