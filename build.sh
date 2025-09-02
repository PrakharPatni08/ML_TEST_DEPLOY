#!/usr/bin/env bash
# filepath: d:\SwarIT\ML\build.sh
echo "🚀 Starting build for Render with Python 3.10..."

#!/usr/bin/env bash
echo "🚀 Forcing Python 3.10 on Render..."

# Try to find and use Python 3.10
if command -v python3.10 &> /dev/null; then
    echo "Found python3.10"
    python3.10 --version
    python3.10 -m pip install --upgrade pip
    python3.10 -m pip install -r requirements.txt
elif [ "$(python --version | grep -o '3\.10')" = "3.10" ]; then
    echo "Using default python (3.10)"
    python --version
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "❌ Python 3.10 not found!"
    python --version
    exit 1
fi

echo "✅ Build completed with Python 3.10!"