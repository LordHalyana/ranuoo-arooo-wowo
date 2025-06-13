import os
import sys
import subprocess
import threading
import signal
import time
from pathlib import Path
from typing import Optional
import shutil

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    Observer = None
    FileSystemEventHandler = object  # Dummy base class to avoid NameError
    WATCHDOG_AVAILABLE = False


def find_service_root(service: str) -> Optional[Path]:
    """Find the root directory for a service, preferring service.toml, else heuristics."""
    cwd = Path.cwd()
    # 1. If service is a directory and contains service.toml, use it
    candidate = cwd / service
    if candidate.is_dir() and (candidate / "service.toml").exists():
        return candidate
    # 2. If service.toml exists in workspace/service/service.toml, use workspace/service
    candidate = cwd / "workspace" / service / "service.toml"
    if candidate.exists():
        return (cwd / "workspace" / service)
    # 3. If service.toml exists in cwd/service, use cwd/service
    candidate = cwd / service / "service.toml"
    if candidate.exists():
        return (cwd / service)
    # 4. If service.toml exists in cwd, use cwd
    candidate = cwd / "service.toml"
    if candidate.exists():
        return cwd
    # 5. If service is a directory, use it
    candidate = cwd / service
    if candidate.is_dir():
        return candidate
    # 6. If service is a file, use its parent
    candidate = cwd / service
    if candidate.is_file():
        return candidate.parent
    return None


def find_entrypoint(service_root: Path) -> Optional[tuple[str, str]]:
    """Return (cmd, entrypoint) for Node (.js) or Python (.py) entry, else None."""
    # Prefer service.toml if present
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
    # Heuristic: look for index.js, main.js, app.js, main.py, app.py
    for fname in ["index.js", "main.js", "app.js", "main.py", "app.py"]:
        f = service_root / fname
        if f.exists():
            if f.suffix == ".js":
                return ("node", str(f))
            elif f.suffix == ".py":
                return (sys.executable, str(f))
    # Fallback: first .js or .py file
    for ext, cmd in [(".js", "node"), (".py", sys.executable)]:
        for f in service_root.glob(f"*{ext}"):
            return (cmd, str(f))
    return None


def stream_output(proc, prefix):
    """Stream process output with prefix."""
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


def run_process(cmd, entrypoint, prefix):
    proc = subprocess.Popen([cmd, entrypoint], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    threads = stream_output(proc, prefix)
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        proc.wait()
    return proc.returncode


class RestartOnChangeHandler(FileSystemEventHandler):
    def __init__(self, restart_callback):
        super().__init__()
        self.restart_callback = restart_callback
    def on_any_event(self, event):
        if not event.is_directory:
            self.restart_callback()


def run(args):
    service = args.service
    watch = getattr(args, "watch", False)
    service_root = find_service_root(service)
    if not service_root:
        print(f"[ERROR] Could not find service root for '{service}'.")
        sys.exit(2)
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
                proc = start()
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
            proc = start()
            threads = stream_output(proc, prefix)
            proc.wait()
        return proc.returncode if proc else 1
    except KeyboardInterrupt:
        if proc:
            try:
                if os.name == "nt":
                    # Windows: terminate the process
                    proc.terminate()
                else:
                    # Unix: send SIGINT to the process group
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
