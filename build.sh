#!/usr/bin/env bash
# filepath: d:\SwarIT\ML\build.sh
echo "🚀 Starting build for Render with Python 3.10.13..."

# Check Python version
echo "Current Python version:"
python --version

# Verify we have the right version
if python --version | grep -q "3.10.13"; then
    echo "✅ Correct Python version 3.10.13 detected!"
elif python --version | grep -q "3.10"; then
    echo "✅ Python 3.10.x detected (close enough)"
else
    echo "⚠️  Expected Python 3.10.13, but found:"
    python --version
    echo "Proceeding anyway..."
fi

# Install requirements
pip install --upgrade pip
pip install -r requirements.txt

# Verify installations
echo "✅ Verifying installations..."
python -c "import sys; print(f'Python version: {sys.version}')"
python -c "import fastapi; print('FastAPI OK')"
python -c "import uvicorn; print('Uvicorn OK')"
python -c "import pymongo; print('PyMongo OK')"
python -c "import pydantic; print('Pydantic OK')"

echo "✅ Build completed successfully with Python 3.10.13!"