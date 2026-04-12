#!/bin/bash

echo "Starting AstroNova application..."
echo "Working directory: $(pwd)"
echo "Python version: $(python --version)"
echo "Contents of /app:"
ls -la /app

echo "Checking Python path..."
python -c "import sys; print('Python path:'); [print(f'  {p}') for p in sys.path]"

echo "Testing minimal main import..."
python -c "
try:
    import main_minimal
    print('✅ main_minimal imported successfully')
    print(f'FastAPI app: {main_minimal.app}')
except ImportError as e:
    print(f'❌ Failed to import main_minimal: {e}')
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f'❌ Error importing main_minimal: {e}')
    import traceback
    traceback.print_exc()
"

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
except Exception as e:
    print(f'❌ Error importing main: {e}')
    import traceback
    traceback.print_exc()
"

# Use the correct working directory and start uvicorn 
echo "Starting AstroNova with fixed configuration..."
echo "Working directory: $(pwd)"
exec python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1