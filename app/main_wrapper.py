import sys
import os

# Ensure the app directory is on the Python path
app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

print(f"Python path: {sys.path}")
print(f"Working directory: {os.getcwd()}")
print(f"App directory: {app_dir}")

# Import with better error handling
try:
    print("Attempting to import main module...")
    from main import app
    print("✅ Successfully imported main module")
except ImportError as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
    raise
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    raise

# Export the app for uvicorn
__all__ = ['app']