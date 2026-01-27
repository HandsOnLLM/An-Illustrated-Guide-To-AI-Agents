from illustrated_agents.chapters.ch1 import TinyAgent


if __name__ == "__main__":
    agent = TinyAgent()
    query = "What is 2 + 2?"
    response = agent.run(query)
    print("==== QUERY ====\n", query, "\n")
    print("==== RESPONSE ====\n", response)
