# LocalAI Microservices Workspace

This directory contains all microservices managed by LocalAI. Each subfolder is a standalone service scaffolded with best practices for Node.js or Python.

## Structure

- Each service has its own folder (e.g., `gateway`, `overlord`, `auth`, `register`).
- Each service contains:
  - `src/` – Source code (controllers, routes, etc.)
  - `public/` – Static assets
  - `views/` – Templates (EJS, etc.)
  - `tests/` – Unit/integration tests
  - `docs/` – Service-specific documentation
  - `service.toml` – Service metadata (name, port, entrypoint, etc.)
  - `package.json` (Node.js) or `requirements.txt` (Python)

## Managing Services

- Scaffold a new service:
  ```powershell
  python main.py init <service-name> --docker-compose
  ```
- Generate or update Docker Compose:
  ```powershell
  python main.py compose generate
  ```
- Start all services:
  ```powershell
  python main.py compose up
  ```

## Adding a Service

1. Run the init command above.
2. Edit the generated files as needed.
3. Add your business logic to `src/`.
4. Update `service.toml` and `index.toml` as needed.

## See Also

- [../README.md](../README.md) – Project overview
- [localdev.md](../localdev.md) – Automation & CLI usage
