import requests
import toml

# Load config values from the project config file
def load_config():
    config = toml.load("config.project.toml")
    return config["ai"]["remote_url"], config["ai"].get("temperature", 0.8)

def query_llama(prompt: str, max_tokens: int = 200):
    remote_url, temperature = load_config()
    payload = {
        "prompt": prompt,
        "n_predict": max_tokens,
        "temperature": temperature
    }

    try:
        response = requests.post(remote_url, json=payload, timeout=60)
        response.raise_for_status()
        return response.json().get("content", "").strip()
    except Exception as e:
        return f"[ERROR] Failed to query model: {e}"
