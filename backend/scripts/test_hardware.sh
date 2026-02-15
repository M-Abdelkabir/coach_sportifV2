#!/bin/bash
# Wrapper to run hardware diagnostic test from the root or scripts directory

# Determine project root
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "-------------------------------------------------------"
echo "  Starting Hardware Diagnostic Tool"
echo "  Location: $PROJECT_ROOT"
echo "-------------------------------------------------------"

# Activate virtual environment if it exists
if [ -d "$PROJECT_ROOT/venv" ]; then
    source "$PROJECT_ROOT/venv/bin/activate"
elif [ -d "$PROJECT_ROOT/../venv" ]; then
    source "$PROJECT_ROOT/../venv/bin/activate"
fi

# Run the python test
python3 "$PROJECT_ROOT/tests/test_hardware.py"

# Deactivate venv
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi
