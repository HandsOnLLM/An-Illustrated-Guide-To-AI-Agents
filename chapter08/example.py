import json
from illustrated_agents import Tools, Memory, LLM, ReAct
from illustrated_agents.chapters.ch5 import TinyAgent as ToolAgent
from illustrated_agents.chapters.ch6 import TinyAgent


def add(a: str, b: str) -> float:
    return float(a) + float(b)


def subtract(a: str, b: str) -> float:
    return float(a) - float(b)


def multiply(a: str, b: str) -> float:
    return float(a) * float(b)


def get_weather(location: str) -> str:
    return f"Weather in {location}: Sunny, 72°F"


if __name__ == "__main__":
    # Both Agents use the same LLM but not share memory or tools
    llm = LLM(model="ollama/gemma3:12b")

    # Math Agent
    math_tools = Tools()
    math_tools.add_tool("add", add, "Adds two numbers: add(a, b)")
    math_tools.add_tool("subtract", subtract, "Subtracts two numbers: subtract(a, b)")
    math_tools.add_tool("multiply", multiply, "Multiplies two numbers: multiply(a, b)")
    memory = Memory()
    math_agent = ToolAgent(llm=llm, tools=math_tools, memory=memory)

    # Convert math agent into a tool
    def ask_math_agent(question: str) -> str:
        """Delegate to the math specialist."""
        return math_agent.run(question)

    # Orchestrator Agent
    tools = Tools()
    tools.add_tool("get_weather", get_weather, "Gets weather: get_weather(city)")
    tools.add_tool("ask_math_agent", ask_math_agent, "Asks the math specialist: ask_math_agent(question)")
    memory = Memory()
    react = ReAct(max_steps=10)
    orchestrator_agent = TinyAgent(llm=llm, tools=tools, memory=memory, planner=react)

    # Run orchestrator agent
    query = "What is 5.12 times 3.9?"
    output = orchestrator_agent.run(query)
    print("==== QUERY ====\n", query, "\n")
    print("==== RESPONSE ====\n", output)

    # Show messages in orchestrator agent memory
    print("\n\n\n==== Orchestrator Agent Messages in Memory ====")
    print(json.dumps(orchestrator_agent.memory.get_messages(), indent=4))

    # Show messages in math agent memory
    print("\n\n\n==== Math Agent Messages in Memory ====")
    print(json.dumps(math_agent.memory.get_messages(), indent=4))
