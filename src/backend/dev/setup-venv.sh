#!/bin/bash
# Setup script for local development virtual environment
# Run from src/backend directory: ./dev/setup-venv.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$BACKEND_DIR"

echo "🚀 Setting up FastShip Backend Development Environment"
echo "=================================================="

# Check Python version
echo "📋 Checking Python version..."
python3 --version

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
if [ -d ".venv" ]; then
    echo "⚠️  .venv directory already exists. Removing it..."
    rm -rf .venv
fi

python3 -m venv .venv

# Activate virtual environment
echo ""
echo "✅ Virtual environment created!"
echo ""
echo "To activate the virtual environment, run:"
echo "  source .venv/bin/activate"
echo ""
echo "Or on Windows:"
echo "  .venv\\Scripts\\activate"
echo ""

# Install dependencies
echo "📥 Installing dependencies..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment: source .venv/bin/activate"
echo "2. Copy .env.example to .env and configure it"
echo "3. Start Docker services: make up (or docker-compose up -d)"
echo "4. Run migrations: make migrate (or alembic upgrade head)"
echo "5. Start the dev server: make dev (or uvicorn app.main:app --reload)"
echo ""
echo "For detailed instructions, see: dev/README.md"
echo ""
