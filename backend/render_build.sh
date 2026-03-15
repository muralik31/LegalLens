#!/bin/bash
# Render build script for LegalLens Backend

set -e  # Exit on error

echo "🚀 Starting Render build..."

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Generate SECRET_KEY if not set
if [ -z "$SECRET_KEY" ]; then
    echo "⚠️  WARNING: SECRET_KEY not set. Generating one..."
    export SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
fi

# Run database migrations
echo "🗄️  Running database migrations..."
alembic upgrade head

echo "✅ Build completed successfully!"
