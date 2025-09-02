#!/usr/bin/env bash
# filepath: d:\SwarIT\ML\build.sh
echo "🚀 Starting build for Render..."

# Upgrade pip first
pip install --upgrade pip

# Install each package individually to catch errors
echo "📦 Installing core dependencies..."
pip install fastapi==0.95.2
pip install uvicorn==0.22.0  
pip install pymongo==4.4.0
pip install langdetect==1.0.9
pip install python-dotenv==1.0.0
pip install requests==2.31.0
pip install pydantic==1.10.9

# Verify installations
echo "✅ Verifying installations..."
python -c "import fastapi; print('FastAPI OK')"
python -c "import uvicorn; print('Uvicorn OK')"
python -c "import pymongo; print('PyMongo OK')"

echo "✅ Build completed successfully!"