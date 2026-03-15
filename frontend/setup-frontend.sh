#!/bin/bash

# LegalLens Frontend Setup Script
# Automatically creates Next.js 14 + TypeScript + TailwindCSS application

set -e

echo "🚀 LegalLens Frontend Setup"
echo "==========================="
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

echo "✅ Node.js $(node --version) detected"

# Check if in frontend directory
if [ ! -f "package.json" ]; then
    echo "❌ package.json not found. Please run this script from the frontend directory."
    exit 1
fi

echo "📦 Installing dependencies..."
npm install

echo ""
echo "📁 Creating directory structure..."
mkdir -p src/app
mkdir -p src/components/ui
mkdir -p src/components/layout
mkdir -p src/lib
mkdir -p src/types
mkdir -p src/store
mkdir -p public

echo ""
echo "✅ Frontend setup complete!"
echo ""
echo "📝 Next steps:"
echo "  1. Copy .env.local.example to .env.local"
echo "  2. Update API_URL in .env.local"
echo "  3. Run: npm run dev"
echo "  4. Visit: http://localhost:3000"
echo ""
