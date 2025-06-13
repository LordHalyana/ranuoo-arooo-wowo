# project_assistant/utils.py
"""Utility functions for path, config, and file operations."""
from pathlib import Path
from typing import Optional
import toml

def find_service_root(service: str) -> Optional[Path]:
    """Find the root directory for a service, preferring service.toml, else heuristics."""
    cwd = Path.cwd()
    candidate = cwd / service
    if candidate.is_dir() and (candidate / "service.toml").exists():
        return candidate
    candidate = cwd / "workspace" / service / "service.toml"
    if candidate.exists():
        return (cwd / "workspace" / service)
    candidate = cwd / service / "service.toml"
    if candidate.exists():
        return (cwd / service)
    candidate = cwd / "service.toml"
    if candidate.exists():
        return cwd
    candidate = cwd / service
    if candidate.is_dir():
        return candidate
    candidate = cwd / service
    if candidate.is_file():
        return candidate.parent
    return None

def load_model_from_config(config_path: str = "config.project.toml") -> Optional[str]:
    try:
        config = toml.load(config_path)
        return config.get("ai", {}).get("model", None)
    except Exception:
        return None
