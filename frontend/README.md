# FastShip Frontend

React frontend application for FastShip shipment management system.

## Prerequisites

- Node.js 20.x or higher
- npm 10.x or higher

## Installation

```bash
npm install
```

**Note**: If you encounter Windows/WSL path issues, install dependencies with:
```bash
npm install --ignore-scripts
```

## Development

Start the development server:

```bash
npm run dev
```

The server will start on `http://localhost:5173` (or the next available port).

## Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Type Checking

```bash
npm run typecheck
```

## Docker

The frontend can be run via Docker Compose:

```bash
docker-compose up -d frontend
```

Access at `http://localhost:5173`

## Configuration

- API URL: Set via `VITE_API_URL` environment variable
- Default: `http://localhost:8000/api`

## Known Issues

- Windows/WSL path warnings during npm install are harmless
- Some TypeScript warnings about missing type definitions are non-critical
