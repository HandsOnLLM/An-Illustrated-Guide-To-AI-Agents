import json

from illustrated_agents import LLM, Memory
from illustrated_agents.chapters.ch4 import TinyAgent


if __name__ == "__main__":
    llm = LLM(model="ollama/gemma3:12b")

    # Add memory to the Agent
    memory = Memory()
    agent = TinyAgent(llm=llm, memory=memory)

    # Multi-turn conversation - the agent remembers!
    query1 = "Hi! We are Maarten and Jay, authors of 'An Illustrated Guide to AI Agents'."
    query2 = "Hi! What are our names?"
    output1 = agent.run(query1)
    output2 = agent.run(query2)
    print("==== QUERY 1 ====\n", query1, "\n")
    print("==== RESPONSE 1 ====\n", output1, "\n")
    print("==== QUERY 2 ====\n", query2, "\n")
    print("==== RESPONSE 2 ====\n", output2)

    # Show messages in memory
    print("\n\n\n==== Messages in Memory ====")
    print(json.dumps(agent.memory.get_messages(), indent=4))
