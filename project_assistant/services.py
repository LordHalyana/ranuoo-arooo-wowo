# project_assistant/services.py
"""Service management: process spawning, file watching, and run logic."""
import sys
import subprocess
import threading
import time
import os
import signal
from pathlib import Path
import shutil
from typing import Optional
from project_assistant.utils import find_service_root, load_model_from_config

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    Observer = None
    FileSystemEventHandler = object
    WATCHDOG_AVAILABLE = False

def stream_output(proc, prefix):
    def stream_reader(stream):
        for line in iter(stream.readline, b""):
            print(f"[{prefix}] {line.decode().rstrip()}")
    threads = []
    for stream in [proc.stdout, proc.stderr]:
        t = threading.Thread(target=stream_reader, args=(stream,))
        t.daemon = True
        t.start()
        threads.append(t)
    return threads

class RestartOnChangeHandler(FileSystemEventHandler):
    def __init__(self, restart_callback):
        super().__init__()
        self.restart_callback = restart_callback
    def on_any_event(self, event):
        if not event.is_directory:
            self.restart_callback()

def run_service(args):
    service = args.service
    watch = getattr(args, "watch", False)
    # Multi-model support: CLI > service.toml > global config
    model = getattr(args, "model", None)
    service_root = find_service_root(service)
    if not service_root:
        print(f"[ERROR] Could not find service root for '{service}'.")
        sys.exit(2)
    # Try to load model from service.toml if not provided by CLI
    if model is None:
        import toml
        toml_path = service_root / "service.toml"
        if toml_path.exists():
            config = toml.load(toml_path)
            model = config.get("model")
    # Fallback to global config.project.toml
    if model is None:
        model = load_model_from_config()
    if model:
        print(f"[INFO] Using model: {model}")
    entry = find_entrypoint(service_root)
    if not entry:
        print(f"[ERROR] No entrypoint found for service '{service}'.")
        sys.exit(3)
    cmd, entrypoint = entry
    prefix = service

    def start():
        return subprocess.Popen([cmd, entrypoint], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    proc = None
    observer = None
    try:
        if watch:
            if cmd == "node":
                # Use nodemon if available
                if shutil.which("nodemon"):
                    proc = subprocess.Popen(["nodemon", entrypoint])
                    proc.wait()
                    return proc.returncode
                elif not WATCHDOG_AVAILABLE:
                    print("[ERROR] --watch requires: pip install watchdog OR npm i -g nodemon")
                    sys.exit(4)
                else:
                    print("[WARN] nodemon not found, falling back to watchdog.")
            # Python or fallback: use watchdog
            if not WATCHDOG_AVAILABLE:
                print("[ERROR] --watch requires: pip install watchdog OR npm i -g nodemon")
                sys.exit(4)
            restart_flag = {"restart": False}
            def restart():
                restart_flag["restart"] = True
                if proc and proc.poll() is None:
                    proc.terminate()
            event_handler = RestartOnChangeHandler(restart)
            observer = Observer()
            observer.schedule(event_handler, str(service_root), recursive=True)
            observer.start()
            while True:
                # Use process group for graceful SIGINT
                if os.name == "nt":
                    proc = subprocess.Popen([cmd, entrypoint], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                else:
                    proc = subprocess.Popen([cmd, entrypoint], preexec_fn=os.setsid, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                threads = stream_output(proc, prefix)
                while proc.poll() is None and not restart_flag["restart"]:
                    time.sleep(0.2)
                if restart_flag["restart"]:
                    restart_flag["restart"] = False
                    proc.terminate()
                    proc.wait()
                    print(f"[{prefix}] Restarting due to file change...")
                else:
                    break
        else:
            # Use process group for graceful SIGINT
            if os.name == "nt":
                proc = subprocess.Popen([cmd, entrypoint], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                proc = subprocess.Popen([cmd, entrypoint], preexec_fn=os.setsid, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            threads = stream_output(proc, prefix)
            proc.wait()
        return proc.returncode if proc else 1
    except KeyboardInterrupt:
        if proc:
            try:
                if os.name == "nt":
                    proc.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    os.killpg(os.getpgid(proc.pid), signal.SIGINT)
            except Exception:
                proc.terminate()
            proc.wait()
        print(f"[{prefix}] Shutting down.")
        return 0
    finally:
        if observer:
            observer.stop()
            observer.join()

def find_entrypoint(service_root: Path) -> Optional[tuple[str, str]]:
    toml_path = service_root / "service.toml"
    if toml_path.exists():
        import toml
        config = toml.load(toml_path)
        entry = config.get("entrypoint")
        if entry:
            entry_path = service_root / entry
            if entry_path.exists():
                if entry_path.suffix == ".js":
                    return ("node", str(entry_path))
                elif entry_path.suffix == ".py":
                    return (sys.executable, str(entry_path))
    for fname in ["index.js", "main.js", "app.js", "main.py", "app.py"]:
        f = service_root / fname
        if f.exists():
            if f.suffix == ".js":
                return ("node", str(f))
            elif f.suffix == ".py":
                return (sys.executable, str(f))
    for ext, cmd in [(".js", "node"), (".py", sys.executable)]:
        for f in service_root.glob(f"*{ext}"):
            return (cmd, str(f))
    return None
