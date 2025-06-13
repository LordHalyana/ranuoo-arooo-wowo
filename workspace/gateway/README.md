# Gateway Microservice

The **gateway** is an Express.js microservice that serves as the entry point to the LocalAI stack.

## Features

- HTTP API on port 3000
- Minimal Express.js setup
- Ready for extension with routes, controllers, and middleware

## Getting Started

1. Install dependencies:
   ```bash
   cd workspace/gateway
   npm install
   ```
2. Start the service:
   ```bash
   npm start
   # or
   node app.js
   ```
3. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

- `app.js` – Main entrypoint
- `src/` – Source code (controllers, routes)
- `public/` – Static assets
- `views/` – Templates (optional)
- `tests/` – Unit/integration tests
- `docs/` – Service documentation
- `service.toml` – Service metadata
- `package.json` – Node.js dependencies and scripts

## Development

- Edit `src/` to add routes and controllers.
- Use `nodemon` for auto-reload during development:
  ```bash
  npx nodemon app.js
  ```

## Environment

- Node.js 20+
- Express 4.x

---

See the root [README.md](../../README.md) for more details on managing the full stack.
