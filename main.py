"""
main.py – LocalAI CLI entrypoint

Provides commands for scaffolding, running, linting, and managing microservices.
"""

import argparse
import sys
import os
from project_assistant.suggester import suggest_code_improvement

def default_test():
    """Run a default LLM test query."""
    from ai_engine.interface import query_llama
    print(query_llama("Write a Python function that returns True if a number is prime."))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Suggest code improvements or run a default test query.",
        epilog="Example: python main.py suggest myscript.py --task optimize"
    )
    parser.add_argument('--version', action='version', version='%(prog)s 1.0.0', help='Show program version and exit.')
    subparsers = parser.add_subparsers(dest='command', required=False)

    # Suggest subcommand
    suggest_parser = subparsers.add_parser('suggest', help="Get code suggestions for a file.")
    suggest_parser.add_argument('filename', help="The file to analyze for suggestions.")
    suggest_parser.add_argument('--task', choices=["refactor", "optimize", "explain"], default="refactor", help="Type of suggestion: refactor, optimize, or explain. Default is refactor.")
    suggest_parser.add_argument('--out', type=str, default=None, help="Optional output file to write suggestions.")

    # Check subcommand
    check_parser = subparsers.add_parser('check', help="Check folder integrity.")
    check_parser.add_argument('--fix', action='store_true', help="Automatically create missing required folders.")
    check_parser.add_argument('--json', action='store_true', help="Output folder integrity results as JSON.")

    # Init subcommand
    init_parser = subparsers.add_parser('init', help="Scaffold a new microservice.")
    init_parser.add_argument('servicename', nargs='?', help="The name of the microservice to initialize.")
    init_parser.add_argument('--docker-compose', dest='docker_compose', action='store_true', help="Add service to docker-compose.yml.")
    init_parser.add_argument('--git', dest='git', action='store_true', help="Initialize a git repository in the new service directory.")
    init_parser.add_argument('--no-git', dest='git', action='store_false', help="Do not initialize git (default).")
    init_parser.add_argument('--interactive', action='store_true', help="Use interactive wizard to configure the microservice.")
    init_parser.set_defaults(docker_compose=False, git=False)

    # Run subcommand
    run_parser = subparsers.add_parser('run', help="Run a service (Node or Python)")
    run_parser.add_argument('service', help="Service name or path to run.")
    run_parser.add_argument('--watch', action='store_true', help="Restart on file changes.")
    run_parser.add_argument('--model', type=str, default=None, help="Model backend to use (overrides config.project.toml fallback).")

    # Lint subcommand
    lint_parser = subparsers.add_parser('lint', help="Lint a microservice (ESLint for JS, Ruff/flake8 for Python)")
    lint_parser.add_argument('service', help="Service name or path to lint.")

    # VS Code tasks subcommand
    tasks_parser = subparsers.add_parser('vscode-tasks', help="Generate VS Code tasks.json for a microservice.")
    tasks_parser.add_argument('service', help="Service name or path to generate tasks for.")

    # Compose subcommand group
    compose_parser = subparsers.add_parser('compose', help="Docker Compose utilities for microservices stack.")
    compose_subparsers = compose_parser.add_subparsers(dest='compose_command', required=True)

    compose_generate = compose_subparsers.add_parser('generate', help="Generate or update docker-compose.yml for all services.")
    compose_generate.add_argument('--force', action='store_true', help="Overwrite docker-compose.yml instead of merging.")

    compose_up = compose_subparsers.add_parser('up', help="Run 'docker compose up' for the stack.")

    args = parser.parse_args()

    # Early default test fallback
    if not args.command:
        default_test()
        sys.exit(0)

    if args.command == "check":
        from project_assistant.folder_checker import check_folder_integrity
        from pathlib import Path
        import toml
        issues = check_folder_integrity(fix=getattr(args, 'fix', False), output_json=getattr(args, 'json', False)) or []
        # Validate service.toml and index.toml
        registry_path = Path("workspace") / "index.toml"
        if registry_path.exists():
            registry = toml.load(registry_path)
            services = registry.get("service", [])
            for svc in services:
                svc_path = Path(svc["path"])
                toml_path = svc_path / "service.toml"
                if not toml_path.exists():
                    issues.append(f"[ERROR] {svc['name']}: Missing service.toml at {toml_path}")
                else:
                    meta = toml.load(toml_path)
                    for field in ["service_name", "port", "language", "entrypoint"]:
                        if field not in meta:
                            issues.append(f"[ERROR] {svc['name']}: service.toml missing '{field}'")
                    # Check registry and toml consistency
                    for field in ["service_name", "port", "language", "entrypoint"]:
                        if field in meta and field in svc and str(meta[field]) != str(svc[field]):
                            issues.append(f"[ERROR] {svc['name']}: Mismatch in '{field}' between service.toml and index.toml")
        if issues:
            if not getattr(args, 'json', False):
                print("\n=== Metadata Validation Issues ===\n")
                for issue in issues:
                    print(issue)
                print(f"\nSummary: {len(issues)} issue(s) found.")
            sys.exit(1)
        else:
            if not getattr(args, 'json', False):
                print("✅ Metadata and folder structure look good.")
                print("Summary: No issues found.")
            sys.exit(0)
    elif args.command == "suggest":
        output = suggest_code_improvement(args.filename, args.task)
        output = f"\n=== Suggested Improvements ({args.task}) ===\n\n{output}"
        if args.out:
            with open(args.out, "w", encoding="utf-8") as outf:
                outf.write(output)
            print(f"Suggestions written to {args.out}")
        else:
            print(output)
        sys.exit(0)
    elif args.command == "init":
        if getattr(args, 'interactive', False):
            import questionary
            service_name = args.servicename or questionary.text("Service name:").ask()
            port = questionary.text("Port:", default="3000").ask()
            language = questionary.select("Language:", choices=["node", "python"], default="node").ask()
            model = questionary.text("Model (optional):", default="").ask() or None
            git = questionary.confirm("Initialize git repo?", default=True).ask()
            docker_compose = questionary.confirm("Add to docker-compose.yml?", default=False).ask()
        else:
            service_name = args.servicename
            port = "3000"
            language = "node"
            model = None
            git = args.git
            docker_compose = args.docker_compose
        from project_assistant.scaffolder import create_microservice
        create_microservice(service_name, git=git, docker_compose=docker_compose, port=port, language=language, model=model)
        sys.exit(0)
    elif args.command == "run":
        from project_assistant.services import run_service
        sys.exit(run_service(args))
    elif args.command == "lint":
        import subprocess
        import shutil
        from pathlib import Path
        service = args.service
        service_root = Path(service)
        if not service_root.exists():
            service_root = Path("workspace") / service
        if not service_root.exists():
            print(f"[ERROR] Service '{service}' not found.")
            sys.exit(2)
        # JS/Node lint
        if (service_root / "package.json").exists():
            if (service_root / "node_modules" / ".bin" / "eslint").exists() or shutil.which("eslint"):
                print("[INFO] Running ESLint...")
                try:
                    subprocess.run(["npx", "eslint", "src"], cwd=service_root, check=True)
                except subprocess.CalledProcessError as e:
                    print("[ERROR] ESLint failed.")
                    sys.exit(e.returncode)
            else:
                print("[WARN] ESLint not found. Skipping JS lint.")
        # Python lint
        py_files = list(service_root.rglob("*.py"))
        if py_files:
            if shutil.which("ruff"):
                print("[INFO] Running Ruff...")
                try:
                    subprocess.run(["ruff", "."], cwd=service_root, check=True)
                except subprocess.CalledProcessError as e:
                    print("[ERROR] Ruff failed.")
                    sys.exit(e.returncode)
            elif shutil.which("flake8"):
                print("[INFO] Running flake8...")
                try:
                    subprocess.run(["flake8", "--max-line-length=120"], cwd=service_root, check=True)
                except subprocess.CalledProcessError as e:
                    print("[ERROR] flake8 failed.")
                    sys.exit(e.returncode)
            else:
                print("[WARN] Ruff/flake8 not found. Skipping Python lint.")
        sys.exit(0)
    elif args.command == "vscode-tasks":
        import json
        from pathlib import Path
        service = args.service
        service_root = Path(service)
        if not service_root.exists():
            service_root = Path("workspace") / service
        if not service_root.exists():
            print(f"[ERROR] Service '{service}' not found.")
            sys.exit(2)
        vscode_dir = service_root / ".vscode"
        vscode_dir.mkdir(exist_ok=True)
        tasks = {
            "version": "2.0.0",
            "tasks": [
                {
                    "label": "Start Service",
                    "type": "shell",
                    "command": "python" if (service_root / "service.toml").exists() and any(f.suffix == ".py" for f in service_root.glob("src/*")) else "npm",
                    "args": ["run", "start"] if (service_root / "package.json").exists() else ["src/app.py"],
                    "group": "build",
                    "problemMatcher": []
                },
                {
                    "label": "Lint Service",
                    "type": "shell",
                    "command": "python" if (service_root / "service.toml").exists() and any(f.suffix == ".py" for f in service_root.glob("src/*")) else "npx",
                    "args": ["ruff", "."] if any(f.suffix == ".py" for f in service_root.glob("src/*")) else ["eslint", "src"],
                    "group": "test",
                    "problemMatcher": []
                }
            ]
        }
        with open(vscode_dir / "tasks.json", "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2)
        print(f"[INFO] VS Code tasks.json generated at {vscode_dir / 'tasks.json'}.")
        sys.exit(0)
    elif args.command == "compose":
        from project_assistant import compose_helper
        if args.compose_command == "generate":
            sys.exit(compose_helper.generate_compose(force=getattr(args, 'force', False)))
        elif args.compose_command == "up":
            sys.exit(compose_helper.run_compose_up())
    else:
        print(f"[WARN] Unknown command '{args.command}'. Running default test.\n")
        default_test()
        sys.exit(1)
