import ollama
from langgraph.graph import StateGraph, START, END

# Helper function to query Ollama
def ask_ollama(prompt, model="gemma3:4b"):
    """Send a prompt to Ollama and return the model's response."""
    response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}])
    return response["message"]["content"].strip()

# -------------------------------
# Shared helper: query Ollama model
# -------------------------------
def query_ollama(prompt, model="gemma3:4b"):
    """Call Ollama with a prompt and return text output."""
    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return response["message"]["content"].strip()

# -------------------------------
# Step 1: Researcher node
# -------------------------------
def researcher_node(state):
    print("\n[Researcher Node Running...]")
    prompt = (
        "You are a cutting-edge AI researcher. "
        "List 3 recent breakthroughs in diffusion models. "
        "Include paper names, methods, or applications where possible."
    )
    findings = query_ollama(prompt)
    print("\n[Researcher Output]\n", findings)
    state["findings"] = findings
    return state


# -------------------------------
# Step 2: Writer node
# -------------------------------
def writer_node(state):
    print("\n[Writer Node Running...]")
    research_notes = state.get("findings", "")
    prompt = (
        "You are a technical blog writer. "
        "Summarize the following diffusion model breakthroughs "
        "into a concise, engaging technical blog post:\n\n"
        f"{research_notes}"
    )
    summary = query_ollama(prompt)
    print("\n[Writer Output]\n", summary)
    state["summary"] = summary
    return state

# -------------------------------
# Step 3: Build LangGraph workflow
# -------------------------------
def build_workflow():
    workflow = StateGraph(dict)

    workflow.add_node("researcher", researcher_node)
    workflow.add_node("writer", writer_node)

    # Define flow: START → Researcher → Writer → END
    workflow.add_edge(START, "researcher")
    workflow.add_edge("researcher", "writer")
    workflow.add_edge("writer", END)

    return workflow


# -------------------------------
# Step 4: Run the graph
# -------------------------------
if __name__ == "__main__":
    print("=== Starting LangGraph + Ollama Workflow ===")
    graph = build_workflow()
    app = graph.compile()
    # Execute with an empty initial state
    final_state = app.invoke({})
    print("\n=== Final Blog Summary ===")
    print(final_state["summary"])
