import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import wikipedia
import re

# -----------------------------
# Step 0: Local model path
# -----------------------------
local_model_path = "/Users/amansawarn/Documents/self_projects/TravelAgent/backend/models/Llama-3.1-8B-Instruct"

# -----------------------------
# Step 1: Load model + tokenizer (optimized for Apple Silicon)
# -----------------------------
device = "mps" if torch.backends.mps.is_available() else "cpu"

tokenizer = AutoTokenizer.from_pretrained(local_model_path, use_fast=True)

# Use bfloat16 on MPS, float16 otherwise
dtype = torch.bfloat16 if device == "mps" else torch.float16

model = AutoModelForCausalLM.from_pretrained(
    local_model_path,
    torch_dtype=dtype,
    device_map="auto",       # automatically place on MPS
    low_cpu_mem_usage=True   # reduce CPU RAM usage
)

# -----------------------------
# Step 2: Define Tools
# -----------------------------
def calculator_tool(expression: str) -> str:
    try:
        if not re.match(r"^[0-9\.\+\-\*\/\(\) ]+$", expression):
            return "Invalid expression"
        return str(eval(expression))
    except Exception as e:
        return f"Error: {str(e)}"

def wikipedia_tool(query: str) -> str:
    try:
        return wikipedia.summary(query, sentences=2)
    except Exception as e:
        return f"Wikipedia error: {str(e)}"

# -----------------------------
# Step 3: Agent function
# -----------------------------
def run_agent(prompt: str, max_new_tokens: int = 200) -> str:
    """
    A simple agent that routes queries to tools or answers directly with the model.
    """
    if prompt.lower().startswith("calc:"):
        expr = prompt[5:].strip()
        return calculator_tool(expr)
    elif prompt.lower().startswith("wiki:"):
        query = prompt[5:].strip()
        return wikipedia_tool(query)
    else:
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():  # disable gradients for speed
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,   # greedy decoding (faster, deterministic)
                temperature=0.0
            )
        return tokenizer.decode(outputs[0], skip_special_tokens=True)

# -----------------------------
# Step 4: Try it out
# -----------------------------
if __name__ == "__main__":
    print("Calculator:", run_agent("calc: 12 * (7 + 3)"))
    print("Wikipedia:", run_agent("wiki: Albert Einstein"))
    print("Chat:", run_agent("Hello, who are you?"))
