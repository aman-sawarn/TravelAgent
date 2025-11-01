import torch
from langchain.agents import initialize_agent, Tool
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_huggingface import HuggingFacePipeline
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

# -----------------------------
# Step 1: Load local model
# -----------------------------
local_model_path = "/Users/amansawarn/Documents/self_projects/TravelAgent/backend/models/Llama-3.1-8B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(local_model_path, use_fast=True)
model = AutoModelForCausalLM.from_pretrained(
    local_model_path,
    dtype=torch.float16,
    device_map="auto"
)

pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=256,
    do_sample=True,
    temperature=0.1,
    top_p=0.95
)

llm = HuggingFacePipeline(pipeline=pipe)

# -----------------------------
# Step 2: Define Tools
# -----------------------------
def calculator(expression: str) -> str:
    try:
        return str(eval(expression))
    except Exception as e:
        return f"Error: {str(e)}"

calc_tool = Tool(
    name="Calculator",
    func=calculator,
    description="Useful for evaluating mathematical expressions. Input: math expression as a string."
)

wiki_wrapper = WikipediaAPIWrapper()
wiki_tool = WikipediaQueryRun(api_wrapper=wiki_wrapper)

# -----------------------------
# Step 3: Create Agent
# -----------------------------
tools = [calc_tool, wiki_tool]

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent="zero-shot-react-description",  # ReAct style agent
    verbose=True
)

# -----------------------------
# Step 4: Try it out
# -----------------------------
if __name__ == "__main__":
    print(agent.run("What is 12 * (7+3)?"))
    print(agent.run("Tell me about Albert Einstein from Wikipedia"))
