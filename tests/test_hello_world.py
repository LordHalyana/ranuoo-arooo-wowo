import subprocess
import time
import requests
import os
import sys
import tempfile
import shutil
import pytest

@pytest.fixture(scope="module")
def demo_service(tmp_path_factory):
    # Setup: scaffold a demo service
    svc_name = "demo-svc"
    subprocess.run([sys.executable, "main.py", "init", svc_name], check=True)
    svc_dir = os.path.join("workspace", svc_name)
    yield svc_name, svc_dir
    # Teardown: remove the service directory
    shutil.rmtree(svc_dir, ignore_errors=True)


def test_hello_world_integration(demo_service):
    svc_name, svc_dir = demo_service
    # Start the service
    proc = subprocess.Popen([sys.executable, "main.py", "run", svc_name])
    time.sleep(2)  # Give the server time to start
    try:
        resp = requests.get("http://localhost:3000/")
        assert resp.status_code == 200
        assert "Welcome to" in resp.text
    finally:
        proc.terminate()
        proc.wait()
