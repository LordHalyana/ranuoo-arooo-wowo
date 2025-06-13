"""
Docker Compose generator and runner for LocalAI microservices stack.
"""
import sys
import subprocess
from pathlib import Path
from typing import Any, List, Dict
from ruamel.yaml import YAML
import toml

WORKSPACE = Path(__file__).parent.parent / "workspace"
INDEX_TOML = WORKSPACE / "index.toml"
COMPOSE_FILE = Path(__file__).parent.parent / "docker-compose.yml"

DEFAULT_IMAGE = "node:20-alpine"
COMPOSE_VERSION = "3.9"
NETWORK_NAME = "localai-net"


def parse_services_from_index(index_path: Path) -> List[Dict[str, Any]]:
    """
    Parse workspace/index.toml and return a list of service dicts.
    Each dict contains: name, port, has_dockerfile, etc.
    """
    index = toml.load(index_path)
    services = []
    for name, meta in index.get("services", {}).items():
        service_dir = WORKSPACE / name
        service_toml = service_dir / "service.toml"
        dockerfile = service_dir / "Dockerfile"
        port = None
        if service_toml.exists():
            config = toml.load(service_toml)
            port = config.get("port")
        services.append({
            "name": name,
            "dir": service_dir,
            "port": port,
            "has_dockerfile": dockerfile.exists(),
        })
    return services


def build_compose_dict(services: List[Dict[str, Any]]) -> dict:
    """
    Build the docker-compose dict for the given services.
    """
    compose = {
        "version": COMPOSE_VERSION,
        "services": {},
        "networks": {NETWORK_NAME: {"driver": "bridge"}},
    }
    for svc in services:
        port = str(svc["port"]) if svc["port"] else "3000"
        block = {
            "ports": [f"{port}:{port}"],
            "environment": [f"PORT={port}"],
            "restart": "unless-stopped",
            "networks": [NETWORK_NAME],
        }
        if svc["has_dockerfile"]:
            block["build"] = str(svc["dir"].relative_to(COMPOSE_FILE.parent))
        else:
            block["image"] = DEFAULT_IMAGE
        compose["services"][svc["name"]] = block
    return compose


def merge_compose(existing: Any, generated: Any) -> Any:
    """
    Merge generated compose YAML into existing, preserving comments and unknown keys.
    Only updates known service blocks and networks.
    """
    # Update or add services
    for svc, block in generated["services"].items():
        existing["services"][svc] = block
    # Remove services not in generated
    for svc in list(existing["services"].keys()):
        if svc not in generated["services"]:
            del existing["services"][svc]
    # Update networks
    existing["networks"] = generated["networks"]
    existing["version"] = generated["version"]
    return existing


def generate_compose(force: bool = False) -> int:
    """
    Generate or update docker-compose.yml based on workspace/index.toml.
    If force is True, overwrite; else merge with existing.
    Returns 0 on success, 1 on skip, 2 on error.
    """
    if not INDEX_TOML.exists():
        print("[ERROR] workspace/index.toml not found.")
        return 2
    services = parse_services_from_index(INDEX_TOML)
    if len(services) < 2:
        print("[INFO] Only one service found, skipping docker-compose generation.")
        return 1
    yaml = YAML()
    yaml.preserve_quotes = True
    compose_dict = build_compose_dict(services)
    if COMPOSE_FILE.exists() and not force:
        with open(COMPOSE_FILE, "r", encoding="utf-8") as f:
            existing = yaml.load(f)
        merged = merge_compose(existing, compose_dict)
        with open(COMPOSE_FILE, "w", encoding="utf-8") as f:
            yaml.dump(merged, f)
    else:
        with open(COMPOSE_FILE, "w", encoding="utf-8") as f:
            yaml.dump(compose_dict, f)
    print(f"[INFO] docker-compose.yml generated with {len(services)} services.")
    return 0


def run_compose_up() -> int:
    """
    Run 'docker compose up' in a subprocess, streaming output.
    Returns the subprocess exit code.
    """
    try:
        proc = subprocess.run(["docker", "compose", "up"], check=True)
        return proc.returncode
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] docker compose up failed: {e}")
        return e.returncode
