import os
import sys
import subprocess
from pathlib import Path
import toml
from typing import Optional

def create_microservice(
    service_name: str,
    git: bool = False,
    docker_compose: bool = False,
    port: str = "3000",
    language: str = "node",
    model: Optional[str] = None
) -> None:
    """Scaffold a new microservice with metadata, Docker, and registry support."""
    base_path = Path("workspace") / service_name
    if base_path.exists():
        print(f"[WARN] Service folder '{base_path}' already exists. Skipping creation.")
        return

    _create_folders(base_path)
    _write_app_files(base_path, service_name, port)
    _write_metadata(base_path, service_name, port, language, model)
    _write_readme(base_path, service_name)
    _write_gitignore(base_path)
    _write_package_json(base_path, service_name)
    _write_dockerfile(base_path, port)

    print(f"[SUCCESS] Microservice '{service_name}' scaffolded at {base_path}.")

    if git:
        _init_git(base_path)
    if docker_compose:
        _update_docker_compose(service_name, port)
    _update_registry(service_name, port, language, model)

def _create_folders(base_path: Path) -> None:
    """Create the necessary folder structure for the microservice."""
    folders = [
        base_path / "src" / "controllers",
        base_path / "src" / "routes",
        base_path / "views",
        base_path / "public",
        base_path / "tests",
        base_path / "docs",
    ]
    try:
        for folder in folders:
            folder.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"[ERROR] Failed to create folders: {e}")
        raise SystemExit(1)

def _write_app_files(base_path: Path, service_name: str, port: str) -> None:
    """Write the main application files: app.js and index.ejs."""
    # Minimal Express.js app template
    app_js = f'''const express = require('express');
const path = require('path');
const app = express();

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, '../views'));
app.use(express.static(path.join(__dirname, '../public')));

app.get('/', (req, res) => {{
    res.render('index', {{ service: '{service_name}' }});
}});

const PORT = process.env.PORT || {port};
app.listen(PORT, () => {{
    console.log(`{service_name} running on port ${{PORT}}`);
}});
'''
    (base_path / "src" / "app.js").write_text(app_js, encoding="utf-8")

    # Minimal EJS template
    ejs_template = f'''<html>
  <head><title>{service_name} Home</title></head>
  <body>
    <h1>Welcome to {service_name}!</h1>
    <p>This is a minimal Express.js + EJS microservice scaffold.</p>
  </body>
</html>
'''
    (base_path / "views" / "index.ejs").write_text(ejs_template, encoding="utf-8")

def _write_metadata(base_path: Path, service_name: str, port: str, language: str, model: Optional[str]) -> None:
    """Write the metadata files: service.toml and README.md."""
    # README
    readme = f"""# {service_name}

Minimal Express.js microservice scaffolded by localdev-ai.

## Getting Started

```bash
cd workspace/{service_name}/src
npm install express ejs
node app.js
```

Open http://localhost:3000
"""
    (base_path / "README.md").write_text(readme, encoding="utf-8")

    # Write service.toml with metadata
    service_toml = {
        "service_name": service_name,
        "port": int(port),
        "language": language,
        "entrypoint": "app.js" if language == "node" else "app.py"
    }
    if model:
        service_toml["model"] = model
    (base_path / "service.toml").write_text(toml.dumps(service_toml), encoding="utf-8")

def _write_readme(base_path: Path, service_name: str) -> None:
    """Write the README.md file."""
    readme = f"""# {service_name}

Minimal Express.js microservice scaffolded by localdev-ai.

## Getting Started

```bash
cd workspace/{service_name}/src
npm install express ejs
node app.js
```

Open http://localhost:3000
"""
    (base_path / "README.md").write_text(readme, encoding="utf-8")

def _write_gitignore(base_path: Path) -> None:
    """Write the .gitignore file."""
    gitignore = "node_modules/\n.env\n"
    (base_path / ".gitignore").write_text(gitignore, encoding="utf-8")

def _write_package_json(base_path: Path, service_name: str) -> None:
    """Write the package.json file."""
    package_json = f'''{{
  "name": "{service_name}",
  "version": "1.0.0",
  "main": "src/app.js",
  "scripts": {{
    "start": "node src/app.js"
  }},
  "dependencies": {{
    "express": "^4.18.0",
    "ejs": "^3.1.8"
  }}
}}'''
    (base_path / "package.json").write_text(package_json, encoding="utf-8")

def _write_dockerfile(base_path: Path, port: str) -> None:
    """Write the Dockerfile."""
    dockerfile = f'''FROM node:20-alpine
WORKDIR /app
COPY package.json ./
RUN npm install --production
COPY . .
EXPOSE {port}
CMD ["npm", "start"]
'''
    (base_path / "Dockerfile").write_text(dockerfile, encoding="utf-8")

def _init_git(base_path: Path) -> None:
    """Initialize a git repository in the microservice folder."""
    try:
        subprocess.run(["git", "init"], cwd=base_path, check=True)
        print(f"[INFO] Initialized git repository in {base_path}.")
    except Exception as e:
        print(f"[WARN] Could not initialize git repo: {e}")

def _update_docker_compose(service_name: str, port: str) -> None:
    """Update the docker-compose.yml file to include the new service."""
    from pathlib import Path
    import yaml
    compose_path = Path("docker-compose.yml")
    service_def = {
        service_name: {
            "build": {
                "context": f"./workspace/{service_name}",
                "dockerfile": "Dockerfile"
            },
            "ports": [f"{port}:{port}"],
            "container_name": service_name
        }
    }
    if compose_path.exists():
        with open(compose_path, "r", encoding="utf-8") as f:
            compose = yaml.safe_load(f) or {}
    else:
        compose = {"version": "3", "services": {}}
    compose.setdefault("services", {}).update(service_def)
    with open(compose_path, "w", encoding="utf-8") as f:
        yaml.dump(compose, f, sort_keys=False)
    print(f"[INFO] Added '{service_name}' to docker-compose.yml.")

def _update_registry(service_name: str, port: str, language: str, model: Optional[str]) -> None:
    """Update the workspace index.toml registry with the new service."""
    from pathlib import Path
    registry_path = Path("workspace") / "index.toml"
    entrypoint = "app.js" if language == "node" else "app.py"
    service_entry = {
        "name": service_name,
        "path": f"workspace/{service_name}",
        "port": int(port),
        "language": language,
        "entrypoint": entrypoint
    }
    if model:
        service_entry["model"] = model
    if registry_path.exists():
        data = toml.load(registry_path)
        if "service" not in data:
            data["service"] = []
        data["service"] = [s for s in data["service"] if s.get("name") != service_name]
        data["service"].append(service_entry)
    else:
        data = {"service": [service_entry]}
    with open(registry_path, "w", encoding="utf-8") as f:
        toml.dump(data, f)
    print(f"[INFO] Registered '{service_name}' in workspace/index.toml.")