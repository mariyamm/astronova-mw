#!/bin/bash

echo "Starting AstroNova application..."
echo "Working directory: $(pwd)"
echo "Python version: $(python --version)"
echo "Contents of /app:"
ls -la /app

echo "Checking Python path..."
python -c "import sys; print('Python path:'); [print(f'  {p}') for p in sys.path]"

echo "Testing main module import..."
python -c "
try:
    import main
    print('✅ main module imported successfully')
    print(f'FastAPI app: {main.app}')
except ImportError as e:
    print(f'❌ Failed to import main: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
except Exception as e:
    print(f'❌ Error importing main: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
"

echo "Starting uvicorn..."
# Try with wrapper first, then fallback to direct main import
echo "Attempting with main_wrapper..."
python -c "import main_wrapper" && exec python -m uvicorn main_wrapper:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 || {
    echo "Wrapper failed, trying direct import..."
    exec python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1
}