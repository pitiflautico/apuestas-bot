#!/bin/bash
# Initial setup script for Sports Props Bot

echo "🎯 Sports Props Intelligence Bot - Setup"
echo "========================================"

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oP '(?<=Python )\d+\.\d+')
required_version="3.10"

if (( $(echo "$python_version < $required_version" | bc -l) )); then
    echo "❌ Python 3.10+ required. Found: $python_version"
    exit 1
fi

echo "✅ Python $python_version found"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "⚠️  Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Dependencies installed"

# Copy environment file
echo ""
echo "Setting up environment file..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ .env file created from template"
    echo "⚠️  Please edit .env with your API keys!"
else
    echo "⚠️  .env file already exists"
fi

# Create data directories
echo ""
echo "Creating data directories..."
mkdir -p data/raw
mkdir -p data/curated
mkdir -p data/results
mkdir -p logs

echo "✅ Data directories created"

# Initialize database
echo ""
echo "Initializing database..."
python3 -c "
import sys
sys.path.insert(0, 'src')
from database import init_db
init_db()
print('✅ Database initialized')
"

echo ""
echo "========================================"
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your API keys"
echo "2. Review config/config.yaml"
echo "3. Run: streamlit run app.py"
echo ""
echo "For data collection: python scripts/collect_data.py"
echo "For predictions: python scripts/run_predictions.py"
echo ""
echo "Good luck! 🍀"
