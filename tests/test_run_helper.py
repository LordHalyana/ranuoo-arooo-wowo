import os
import tempfile
import shutil
import sys
import types
import pytest
from pathlib import Path
from run_helper import find_service_root, find_entrypoint, run


def test_find_service_root(tmp_path):
    # service.toml in subdir
    service_dir = tmp_path / "foo"
    service_dir.mkdir()
    (service_dir / "service.toml").write_text("[main]\n")
    orig = os.getcwd()
    os.chdir(tmp_path)
    try:
        root = find_service_root("foo")
        assert root == service_dir
    finally:
        os.chdir(orig)


def test_find_entrypoint_toml(tmp_path):
    # service.toml with entrypoint
    (tmp_path / "service.toml").write_text("entrypoint = 'main.py'\n")
    (tmp_path / "main.py").write_text("print('hi')\n")
    entry = find_entrypoint(tmp_path)
    assert entry[1].endswith("main.py")
    assert entry[0] == sys.executable


def test_find_entrypoint_heuristic(tmp_path):
    (tmp_path / "main.js").write_text("console.log('hi')\n")
    entry = find_entrypoint(tmp_path)
    assert entry[1].endswith("main.js")
    assert entry[0] == "node"


def test_run_no_service_root(monkeypatch):
    class Args: service = "notfound"; watch = False
    with pytest.raises(SystemExit) as e:
        run(Args())
    assert e.value.code == 2


def test_run_no_entrypoint(tmp_path, monkeypatch):
    class Args: service = str(tmp_path); watch = False
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as e:
        run(Args())
    assert e.value.code == 3

# Note: Integration tests for process spawning and --watch are omitted for safety.

def test_find_entrypoint_minimal(tmp_path):
    # Create a dummy Node service
    (tmp_path / "main.js").write_text("console.log('hi')\n")
    cmd, entry = find_entrypoint(tmp_path)
    assert cmd == "node"
    assert entry.endswith("main.js")

    # Create a dummy Python service
    (tmp_path / "main.py").write_text("print('hi')\n")
    cmd, entry = find_entrypoint(tmp_path)
    assert cmd == sys.executable
    assert entry.endswith("main.py")

    # service.toml with entrypoint
    (tmp_path / "service.toml").write_text("entrypoint = 'main.py'\n")
    cmd, entry = find_entrypoint(tmp_path)
    assert cmd == sys.executable
    assert entry.endswith("main.py")
