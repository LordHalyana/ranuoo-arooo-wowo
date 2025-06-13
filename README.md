# LocalAI: Modern Microservices Automation Platform

LocalAI is a developer tool for rapidly scaffolding, running, and managing AI-powered microservices using Python and Node.js. It provides CLI automation, Docker Compose integration, and code improvement suggestions via LLMs.

## Features

- **Microservice scaffolding**: Quickly create new Node.js or Python services with best-practice structure.
- **Automated code suggestions**: Refactor, optimize, or explain code using LLMs (CodeLlama, etc).
- **Docker Compose orchestration**: Generate and manage a multi-service stack with a single command.
- **File watching & auto-restart**: Run services with live reload for rapid development.
- **Metadata validation**: Ensure all services have correct config and structure.
- **VS Code integration**: Generate tasks.json for easy development.

## Quick Start

1. **Install dependencies**

   ```powershell
   pip install -r requirements.txt
   # or
   poetry install
   ```

2. **Scaffold a new service**

   ```powershell
   python main.py init myservice --docker-compose
   ```

3. **Run all services**

   ```powershell
   python main.py compose up
   ```

4. **Get code suggestions**
   ```powershell
   python main.py suggest path/to/file.py --task refactor
   ```

## Documentation

- See `localdev.md` for automation and usage details.
- See `workspace/README.md` for Docker Compose and service management.
- Each service folder contains its own `README.md` for service-specific docs.

## Contributing

Pull requests and issues are welcome! Please see `CONTRIBUTING.md` (coming soon).

## License

MIT License
