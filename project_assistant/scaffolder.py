def create_microservice(service_name, git=False, docker_compose=False, port="3000"):
    import os
    import sys
    from pathlib import Path
    import subprocess

    base_path = Path("workspace") / service_name
    if base_path.exists():
        print(f"[WARN] Service folder '{base_path}' already exists. Skipping creation.")
        return

    # Folder structure
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

    # .gitignore
    gitignore = "node_modules/\n.env\n"
    (base_path / ".gitignore").write_text(gitignore, encoding="utf-8")

    # package.json
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

    # Dockerfile
    dockerfile = f'''FROM node:20-alpine
WORKDIR /app
COPY package.json ./
RUN npm install --production
COPY . .
EXPOSE {port}
CMD ["npm", "start"]
'''
    (base_path / "Dockerfile").write_text(dockerfile, encoding="utf-8")

    print(f"[SUCCESS] Microservice '{service_name}' scaffolded at {base_path}.")

    # Git initialization if requested
    if git:
        try:
            subprocess.run(["git", "init"], cwd=base_path, check=True)
            print(f"[INFO] Initialized git repository in {base_path}.")
        except Exception as e:
            print(f"[WARN] Could not initialize git repo: {e}")

    # Docker Compose support if requested
    if docker_compose:
        compose_path = Path("docker-compose.yml")
        import yaml
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

    # --- Registry update ---
    import toml
    registry_path = Path("workspace") / "index.toml"
    service_entry = {
        "name": service_name,
        "path": f"workspace/{service_name}",
        "port": int(port),
        "description": f"Express.js {service_name} microservice.",
        "entrypoint": "app.js"
    }
    if registry_path.exists():
        with open(registry_path, "r", encoding="utf-8") as f:
            registry = toml.load(f)
    else:
        registry = {"services": {}}
    registry["services"].setdefault(service_name, {}).update(service_entry)
    with open(registry_path, "w", encoding="utf-8") as f:
        toml.dump(registry, f)
    print(f"[INFO] Registered '{service_name}' in workspace/index.toml.")