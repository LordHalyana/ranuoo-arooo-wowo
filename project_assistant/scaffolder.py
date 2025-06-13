def create_microservice(service_name):
    import os
    import sys
    from pathlib import Path

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

const PORT = process.env.PORT || 3000;
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
EXPOSE 3000
CMD ["npm", "start"]
'''
    (base_path / "Dockerfile").write_text(dockerfile, encoding="utf-8")

    print(f"[SUCCESS] Microservice '{service_name}' scaffolded at {base_path}.")