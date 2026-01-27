from illustrated_agents.llm import LLM
from illustrated_agents.chapters.ch2 import TinyAgent


if __name__ == "__main__":
    llm = LLM(model="ollama/gemma3:12b")
    agent = TinyAgent(llm=llm)
    query = "What is 2 + 2?"
    response = agent.run(query)
    print("==== QUERY ====\n", query, "\n")
    print("==== RESPONSE ====\n", response)
