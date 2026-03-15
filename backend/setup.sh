#!/bin/bash

# LegalLens Backend Setup Script

set -e  # Exit on error

echo "🚀 LegalLens Backend v3.0 Setup"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version
echo "📌 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    echo -e "${GREEN}✓${NC} Python $python_version found"
else
    echo -e "${RED}✗${NC} Python $required_version or higher is required"
    exit 1
fi

# Check PostgreSQL
echo ""
echo "📌 Checking PostgreSQL..."
if command -v psql &> /dev/null; then
    echo -e "${GREEN}✓${NC} PostgreSQL is installed"
else
    echo -e "${YELLOW}⚠${NC} PostgreSQL not found. Please install PostgreSQL 14+"
    echo "   macOS: brew install postgresql@14"
    echo "   Ubuntu: sudo apt-get install postgresql-14"
fi

# Create virtual environment
echo ""
echo "📦 Setting up virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
else
    echo -e "${YELLOW}⚠${NC} Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✓${NC} Dependencies installed"

# Setup environment file
echo ""
echo "⚙️  Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env

    # Generate secret key
    secret_key=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

    # Update .env with generated secret key (macOS compatible)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/your-secret-key-here-generate-with-openssl-rand-hex-32/$secret_key/" .env
    else
        sed -i "s/your-secret-key-here-generate-with-openssl-rand-hex-32/$secret_key/" .env
    fi

    echo -e "${GREEN}✓${NC} .env file created with generated SECRET_KEY"
    echo -e "${YELLOW}⚠${NC} Please edit .env and configure:"
    echo "   - DATABASE_URL (if different from default)"
    echo "   - LLM_PROVIDER and API keys (if using OpenAI/Anthropic)"
    echo "   - STORAGE_PROVIDER and credentials (if using S3/R2)"
else
    echo -e "${YELLOW}⚠${NC} .env file already exists (skipping)"
fi

# Create uploads directory
echo ""
echo "📁 Creating uploads directory..."
mkdir -p uploads
echo -e "${GREEN}✓${NC} Uploads directory created"

# Setup database
echo ""
echo "🗄️  Database setup..."
read -p "Do you want to create the database now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter database name [legallens]: " db_name
    db_name=${db_name:-legallens}

    read -p "Enter PostgreSQL user [postgres]: " db_user
    db_user=${db_user:-postgres}

    # Create database
    createdb -U "$db_user" "$db_name" 2>/dev/null && \
        echo -e "${GREEN}✓${NC} Database '$db_name' created" || \
        echo -e "${YELLOW}⚠${NC} Database '$db_name' may already exist"

    # Run migrations
    echo "Running database migrations..."
    alembic revision --autogenerate -m "Initial migration" 2>/dev/null || true
    alembic upgrade head
    echo -e "${GREEN}✓${NC} Database migrations applied"
fi

# Test installation
echo ""
echo "🧪 Testing installation..."
python3 -c "
from app.config import settings
from app.models import Base
print('✓ Configuration loaded successfully')
print('✓ Models imported successfully')
print(f'✓ Database URL: {settings.DATABASE_URL[:30]}...')
print(f'✓ LLM Provider: {settings.LLM_PROVIDER}')
print(f'✓ Storage Provider: {settings.STORAGE_PROVIDER}')
"

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✓ Setup completed successfully!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "📝 Next steps:"
echo "   1. Review and update .env file if needed"
echo "   2. Start the server:"
echo "      uvicorn app.main_v3:app --reload"
echo "   3. Visit http://localhost:8000/docs for API documentation"
echo ""
echo "🔗 Useful commands:"
echo "   - Start server: uvicorn app.main_v3:app --reload"
echo "   - Run tests: PYTHONPATH=. pytest"
echo "   - Create migration: alembic revision --autogenerate -m 'description'"
echo "   - Apply migrations: alembic upgrade head"
echo ""
echo "📚 Documentation: README_V3.md"
echo ""
