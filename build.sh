#!/usr/bin/env bash
# filepath: d:\SwarIT\ML\build.sh
echo "🚀 Starting lightweight build for Render Free Tier..."

# Install requirements (much lighter now)
pip install -r requirements.txt

# No need for heavy models anymore
echo "✅ Lightweight build completed successfully!"
echo "💡 Using keyword-based models optimized for 512MB RAM limit"