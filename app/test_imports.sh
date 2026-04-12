#!/bin/bash
echo "🧪 Testing import fixes..."

cd /app 2>/dev/null || cd .

echo ""
echo "1️⃣ Testing fallback.py..."
python -c "
try:
    import fallback
    print('✅ fallback.py imports successfully')
    print(f'App: {fallback.app}')
except Exception as e:
    print(f'❌ fallback.py failed: {e}')
    import traceback
    traceback.print_exc()
"

echo ""
echo "2️⃣ Testing main_minimal.py..."
python -c "
try:
    import main_minimal
    print('✅ main_minimal.py imports successfully')
    print(f'App: {main_minimal.app}')
except Exception as e:
    print(f'❌ main_minimal.py failed: {e}')
    import traceback
    traceback.print_exc()
"

echo ""
echo "3️⃣ Testing main.py..."
python -c "
try:
    import main
    print('✅ main.py imports successfully')
    print(f'App: {main.app}')
except Exception as e:
    print(f'❌ main.py failed: {e}')
    import traceback
    traceback.print_exc()
"

echo ""
echo "🎯 Testing uvicorn startup..."
echo "Starting server on port 8001 for 5 seconds..."
timeout 5 python -m uvicorn fallback:app --host 0.0.0.0 --port 8001 &
SERVER_PID=$!
sleep 2
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
fi
kill $SERVER_PID 2>/dev/null || true
wait $SERVER_PID 2>/dev/null || true

echo ""
echo "🎉 Import test complete!"