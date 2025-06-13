import os
from ai_engine.interface import query_llama

def suggest_code_improvement(file_path: str, task: str = "refactor") -> str:
    if not os.path.isfile(file_path):
        return f"[ERROR] File not found: {file_path}"

    with open(file_path, "r", encoding="utf-8") as f:
        file_content = f.read()

    instruction = f"{task.capitalize()} the following Python code."
    prompt = f"{instruction}\n\n{file_content}"
    return query_llama(prompt)
