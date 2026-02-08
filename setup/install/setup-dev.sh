#!/bin/bash
# MemScreen Development Environment Setup Script
# For developers who want to contribute to MemScreen

set -e

echo "🛠️  MemScreen Development Environment Setup"
echo "=========================================="
echo ""

# Detect OS
OS="$(uname -s)"

# Check Python
echo "🐍 Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found!"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "✓ $PYTHON_VERSION"

# Create virtual environment
echo ""
echo "📦 Creating development virtual environment..."
if [ -d "venv" ]; then
    echo "✓ venv already exists, removing..."
    rm -rf venv
fi

python3 -m venv venv
source venv/bin/activate

# Upgrade pip and install tools
echo ""
echo "🔧 Installing development tools..."
pip install --upgrade pip setuptools wheel
pip install pytest pytest-cov black flake8 mypy pylint

# Install dependencies
echo ""
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Install development dependencies
if [ -f "requirements-dev.txt" ]; then
    pip install -r requirements-dev.txt
else
    echo "⚠️  requirements-dev.txt not found, installing common dev tools..."
    pip install pytest pytest-cov black flake8 mypy pylint pre-commit
fi

# Setup pre-commit hooks if available
echo ""
echo "🔗 Setting up development tools..."
if [ -f ".pre-commit-config.yaml" ]; then
    pip install pre-commit
    pre-commit install
    echo "✓ Pre-commit hooks installed"
fi

# Check for optional development tools
echo ""
echo "🔍 Checking optional tools..."

# Ollama
if command -v ollama &> /dev/null; then
    echo "✓ Ollama installed"
    if ! ollama list > /dev/null 2>&1; then
        echo "⚠️  Ollama not running, start with: ollama serve"
    fi
else
    echo "⚠️  Ollama not found (optional, for testing)"
    echo "   Install from: https://ollama.com/download"
fi

# Docker
if command -v docker &> /dev/null; then
    echo "✓ Docker installed"
    if ! docker info &> /dev/null; then
        echo "⚠️  Docker not running, start with: open Docker Desktop"
    fi
else
    echo "⚠️  Docker not found (optional)"
fi

# Run tests
echo ""
echo "🧪 Running tests..."
if [ -d "tests" ]; then
    pytest tests/ -v --tb=short || echo "⚠️  Some tests failed, but setup complete"
else
    echo "⚠️  No tests directory found"
fi

# Code formatting check
echo ""
echo "🎨 Checking code formatting..."
if [ -d "memscreen" ]; then
    echo "Running black (code formatter)..."
    black --check memscreen/ || echo "⚠️  Some files need formatting. Run: black memscreen/"
else
    echo "⚠️  memscreen directory not found"
fi

# Create development config
echo ""
echo "⚙️  Setting up development configuration..."
if [ ! -f "config.yaml" ]; then
    if [ -f "config_example.yaml" ]; then
        cp config_example.yaml config.yaml
        echo "✓ Created config.yaml"
    fi
fi

# Summary
echo ""
echo "=========================================="
echo "✅ Development environment ready!"
echo ""
echo "🚀 Development Commands:"
echo "   source venv/bin/activate  # Activate virtual environment"
echo "   python start.py             # Run MemScreen"
echo "   pytest tests/              # Run tests"
echo "   black memscreen/           # Format code"
echo "   flake8 memscreen/          # Check code style"
echo ""
echo "📚 Development Resources:"
echo "   - Architecture: docs/ARCHITECTURE.md"
echo "   - API Docs: docs/CORE_API.md"
echo "   - Testing: docs/TESTING_GUIDE.md"
echo "   - Contributing: GitHub Issues/Discussions"
echo ""
echo "🐛 Bug Reports:"
echo "   https://github.com/smileformylove/MemScreen/issues"
echo ""
