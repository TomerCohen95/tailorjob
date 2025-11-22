#!/bin/bash

# TailorJob Backend Setup Script

echo "🚀 Setting up TailorJob Backend..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11 or later."
    exit 1
fi

echo "✓ Python found: $(python3 --version)"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from example..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Please edit backend/.env with your actual credentials:"
    echo "   - SUPABASE_URL"
    echo "   - SUPABASE_KEY"
    echo "   - UPSTASH_REDIS_URL"
    echo "   - AZURE_OPENAI_ENDPOINT"
    echo "   - AZURE_OPENAI_KEY"
    echo ""
else
    echo "✓ .env file already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit backend/.env with your credentials"
echo "2. Run the database migration in Supabase Dashboard"
echo "3. Start the server: uvicorn app.main:app --reload"
echo ""
echo "To activate the virtual environment later, run:"
echo "  source venv/bin/activate"
echo ""