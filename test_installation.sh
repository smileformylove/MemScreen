#!/bin/bash

# MemScreen macOS Installation Test Script
# This script verifies that all dependencies are correctly installed

echo "🧪 MemScreen macOS Installation Test"
echo "====================================="
echo ""

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to check if a command exists
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 is installed"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $1 is NOT installed"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Function to check Python version
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

        if [ "$PYTHON_MAJOR" -gt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 8 ]); then
            echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION (required: 3.8+)"
            TESTS_PASSED=$((TESTS_PASSED + 1))
            return 0
        else
            echo -e "${RED}✗${NC} Python $PYTHON_VERSION (required: 3.8+)"
            TESTS_FAILED=$((TESTS_FAILED + 1))
            return 1
        fi
    else
        echo -e "${RED}✗${NC} Python3 is NOT installed"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Function to check Ollama models
check_ollama_models() {
    if command -v ollama &> /dev/null; then
        echo -e "${GREEN}✓${NC} Ollama is installed"
        TESTS_PASSED=$((TESTS_PASSED + 1))

        # Check if Ollama service is running
        if ollama list &> /dev/null; then
            echo -e "${GREEN}✓${NC} Ollama service is running"

            # Check for required models
            MODELS=$(ollama list)
            if echo "$MODELS" | grep -q "qwen2.5vl"; then
                echo -e "${GREEN}✓${NC} qwen2.5vl:3b model is installed"
                TESTS_PASSED=$((TESTS_PASSED + 1))
            else
                echo -e "${YELLOW}⚠${NC} qwen2.5vl:3b model is NOT installed (run: ollama pull qwen2.5vl:3b)"
                TESTS_FAILED=$((TESTS_FAILED + 1))
            fi

            if echo "$MODELS" | grep -q "nomic-embed-text"; then
                echo -e "${GREEN}✓${NC} nomic-embed-text model is installed"
                TESTS_PASSED=$((TESTS_PASSED + 1))
            else
                echo -e "${YELLOW}⚠${NC} nomic-embed-text model is NOT installed (run: ollama pull nomic-embed-text)"
                TESTS_FAILED=$((TESTS_FAILED + 1))
            fi
        else
            echo -e "${RED}✗${NC} Ollama service is NOT running (run: ollama serve)"
            TESTS_FAILED=$((TESTS_FAILED + 2))
        fi
        return 0
    else
        echo -e "${RED}✗${NC} Ollama is NOT installed (run: brew install ollama)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Function to check Python packages
check_python_packages() {
    echo ""
    echo "Checking Python packages..."

    # Check if we're in the MemScreen directory
    if [ ! -f "requirements.txt" ]; then
        echo -e "${RED}✗${NC} Not in MemScreen directory (requirements.txt not found)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi

    # Key packages to check (format: "package_name:import_name")
    PACKAGES=(
        "kivy:kivy"
        "opencv-python:cv2"
        "Pillow:PIL"
        "ollama:ollama"
        "chromadb:chromadb"
    )

    for package_info in "${PACKAGES[@]}"; do
        package_name=$(echo $package_info | cut -d: -f1)
        import_name=$(echo $package_info | cut -d: -f2)

        if python3 -c "import $import_name" 2>/dev/null; then
            echo -e "${GREEN}✓${NC} $package_name is installed"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo -e "${RED}✗${NC} $package_name is NOT installed"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    done
}

# Function to check directories
check_directories() {
    echo ""
    echo "Checking MemScreen directories..."

    DIRS=(
        "memscreen"
        "db"
    )

    for dir in "${DIRS[@]}"; do
        if [ -d "$dir" ]; then
            echo -e "${GREEN}✓${NC} Directory '$dir' exists"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo -e "${YELLOW}⚠${NC} Directory '$dir' does not exist (will be created on first run)"
        fi
    done
}

# Run tests
echo "1. Checking system prerequisites..."
echo "-----------------------------------"
check_python
check_command "git"
check_command "brew"

echo ""
echo "2. Checking Ollama installation..."
echo "-----------------------------------"
check_ollama_models

echo ""
echo "3. Checking Python packages..."
echo "-----------------------------------"
check_python_packages

echo ""
echo "4. Checking MemScreen structure..."
echo "-----------------------------------"
check_directories

# Summary
echo ""
echo "====================================="
echo "Test Summary"
echo "====================================="
echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed! You're ready to run MemScreen.${NC}"
    echo ""
    echo "To start MemScreen, run:"
    echo "  python start_kivy.py"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some tests failed. Please fix the issues above.${NC}"
    echo ""
    echo "Common fixes:"
    echo "  - Install missing packages: pip install -r requirements.txt"
    echo "  - Pull Ollama models: ollama pull qwen2.5vl:3b && ollama pull nomic-embed-text"
    echo "  - Start Ollama service: ollama serve"
    exit 1
fi
