import os
import shutil
import tempfile
from pathlib import Path
import pytest
from ruamel.yaml import YAML
from project_assistant import compose_helper

def setup_mock_service(tmpdir, name, port=3000, dockerfile=True):
    svc_dir = tmpdir / "workspace" / name
    svc_dir.mkdir(parents=True, exist_ok=True)
    (svc_dir / "service.toml").write_text(f"""port = {port}\n""")
    if dockerfile:
        (svc_dir / "Dockerfile").write_text("FROM node:20-alpine\n")

def setup_index(tmpdir, services):
    index = {"services": {}}
    for svc in services:
        index["services"][svc] = {}
    import toml
    (tmpdir / "workspace" / "index.toml").write_text(toml.dumps(index))

def test_compose_idempotency(tmp_path):
    # Setup workspace with 2 services
    setup_mock_service(tmp_path, "svc1", 3001)
    setup_mock_service(tmp_path, "svc2", 3002)
    setup_index(tmp_path, ["svc1", "svc2"])
    compose_path = tmp_path / "docker-compose.yml"
    # Patch paths in compose_helper
    compose_helper.WORKSPACE = tmp_path / "workspace"
    compose_helper.INDEX_TOML = compose_helper.WORKSPACE / "index.toml"
    compose_helper.COMPOSE_FILE = compose_path
    # First generation
    assert compose_helper.generate_compose(force=True) == 0
    with open(compose_path, "rb") as f:
        first = f.read()
    # Second generation (should not change file)
    assert compose_helper.generate_compose(force=False) == 0
    with open(compose_path, "rb") as f:
        second = f.read()
    assert first == second

def test_compose_skips_with_one_service(tmp_path):
    setup_mock_service(tmp_path, "svc1", 3001)
    setup_index(tmp_path, ["svc1"])
    compose_helper.WORKSPACE = tmp_path / "workspace"
    compose_helper.INDEX_TOML = compose_helper.WORKSPACE / "index.toml"
    compose_helper.COMPOSE_FILE = tmp_path / "docker-compose.yml"
    assert compose_helper.generate_compose(force=True) == 1
    assert not compose_helper.COMPOSE_FILE.exists()
