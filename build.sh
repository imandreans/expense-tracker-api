#!/bin/bash
# scripts/build.sh

set -e  # Exit immediately if a command exits with a non-zero status

echo "🔧 Starting Netlify build with uv..."

# Install uv if not already present
if ! command -v uv &> /dev/null; then
    echo "📥 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
else
    echo "✅ uv already installed"
fi

# Optional: Display uv and Python versions for debugging
uv --version
python --version

# Install project dependencies (respects uv.lock if present)
echo "📦 Syncing dependencies with uv..."
uv sync --frozen

# Optional: Build static assets (e.g., if you have a frontend)
# Uncomment and adjust if needed:
# npm install && npm run build

# Run your application or build command
# Replace 'your_app.py' with your actual entry point
echo "🚀 Running your Python application..."
uv run python your_app.py

# If you're building a static site or generating output,
# make sure files end up in the publish directory (e.g., 'public/')
# Example:
# uv run python generate_site.py --output public/

echo "✅ Build completed successfully!"