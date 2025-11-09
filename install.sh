#!/bin/bash
# Auto-installer for Sports Props Bot with Python 3

set -e  # Exit on error

echo "🎯 Sports Props Intelligence Bot - Auto Installer"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Detect Python 3
echo "🔍 Detecting Python 3..."

PYTHON_CMD=""

# Try different Python 3 commands
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '(?<=Python )\d+\.\d+')
    print_success "Found python3 - Version $PYTHON_VERSION"
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version 2>&1 | grep -oP '(?<=Python )\d+\.\d+')
    if [[ $PYTHON_VERSION == 3.* ]]; then
        PYTHON_CMD="python"
        print_success "Found python (version 3) - Version $PYTHON_VERSION"
    else
        print_error "Python 3 not found. Python 2 detected: $PYTHON_VERSION"
        echo "Please install Python 3.10 or higher"
        exit 1
    fi
else
    print_error "Python not found!"
    echo "Please install Python 3.10 or higher from https://www.python.org/"
    exit 1
fi

# Check Python version is >= 3.10
MAJOR_VERSION=$(echo $PYTHON_VERSION | cut -d. -f1)
MINOR_VERSION=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$MAJOR_VERSION" -lt 3 ] || ([ "$MAJOR_VERSION" -eq 3 ] && [ "$MINOR_VERSION" -lt 10 ]); then
    print_error "Python $PYTHON_VERSION is too old. Requires Python 3.10+"
    echo "Please upgrade Python from https://www.python.org/"
    exit 1
fi

print_success "Python version check passed: $PYTHON_VERSION >= 3.10"

# Detect pip
echo ""
echo "🔍 Detecting pip..."

PIP_CMD=""

if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
    print_success "Found pip3"
elif command -v pip &> /dev/null; then
    PIP_CMD="pip"
    print_success "Found pip"
else
    print_error "pip not found!"
    echo "Installing pip..."
    $PYTHON_CMD -m ensurepip --upgrade || {
        print_error "Failed to install pip"
        echo "Please install pip manually: https://pip.pypa.io/en/stable/installation/"
        exit 1
    }
    PIP_CMD="$PYTHON_CMD -m pip"
fi

# Upgrade pip
echo ""
echo "📦 Upgrading pip..."
$PIP_CMD install --upgrade pip
print_success "pip upgraded"

# Create virtual environment
echo ""
echo "🌍 Creating virtual environment..."

if [ -d "venv" ]; then
    print_info "Virtual environment already exists"
    read -p "Do you want to recreate it? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        $PYTHON_CMD -m venv venv
        print_success "Virtual environment recreated"
    fi
else
    $PYTHON_CMD -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "🔌 Activating virtual environment..."

if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    print_success "Virtual environment activated (Unix)"
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
    print_success "Virtual environment activated (Windows)"
else
    print_error "Could not find activation script"
    exit 1
fi

# Install core dependencies
echo ""
echo "📦 Installing core dependencies..."
echo "This may take a few minutes..."

pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

print_success "All dependencies installed!"

# Check if optional ML dependencies are desired
echo ""
read -p "Do you want to install optional ML libraries (XGBoost, LightGBM)? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📦 Installing ML libraries..."
    pip install xgboost lightgbm
    print_success "ML libraries installed"
else
    print_info "Skipped ML libraries (can install later with: pip install xgboost lightgbm)"
fi

# Create directories
echo ""
echo "📁 Creating data directories..."

mkdir -p data/raw/nba
mkdir -p data/raw/acb
mkdir -p data/raw/laliga
mkdir -p data/raw/tennis
mkdir -p data/curated
mkdir -p data/results
mkdir -p data/models
mkdir -p logs
mkdir -p docs

print_success "Directories created"

# Setup environment file
echo ""
echo "⚙️ Setting up environment file..."

if [ -f ".env" ]; then
    print_info ".env file already exists"
    read -p "Do you want to overwrite it? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp .env.example .env
        print_success ".env file created from template"
    fi
else
    cp .env.example .env
    print_success ".env file created from template"
fi

# Initialize database
echo ""
echo "🗄️ Initializing database..."

$PYTHON_CMD -c "
import sys
sys.path.insert(0, 'src')
from database import init_db
init_db()
print('Database initialized successfully')
" && print_success "Database initialized" || print_error "Database initialization failed"

# Verify installation
echo ""
echo "🔍 Verifying installation..."

$PYTHON_CMD -c "
import sys
print(f'Python: {sys.version}')

# Test imports
try:
    import pandas
    print(f'✅ pandas {pandas.__version__}')
except ImportError as e:
    print(f'❌ pandas: {e}')

try:
    import numpy
    print(f'✅ numpy {numpy.__version__}')
except ImportError as e:
    print(f'❌ numpy: {e}')

try:
    import streamlit
    print(f'✅ streamlit {streamlit.__version__}')
except ImportError as e:
    print(f'❌ streamlit: {e}')

try:
    import sqlalchemy
    print(f'✅ sqlalchemy {sqlalchemy.__version__}')
except ImportError as e:
    print(f'❌ sqlalchemy: {e}')

try:
    import scipy
    print(f'✅ scipy {scipy.__version__}')
except ImportError as e:
    print(f'❌ scipy: {e}')

# Optional ML
try:
    import xgboost
    print(f'✅ xgboost {xgboost.__version__} (optional)')
except ImportError:
    print('ℹ️  xgboost not installed (optional)')

try:
    import lightgbm
    print(f'✅ lightgbm {lightgbm.__version__} (optional)')
except ImportError:
    print('ℹ️  lightgbm not installed (optional)')
"

# Print next steps
echo ""
echo "=================================================="
print_success "Installation Complete! 🎉"
echo "=================================================="
echo ""
echo "📋 Next Steps:"
echo ""
echo "1️⃣  Edit .env file with your API keys:"
echo "   nano .env"
echo ""
echo "2️⃣  Download historical data (optional but recommended):"
echo "   python3 scripts/populate_historical_data.py --quick"
echo ""
echo "3️⃣  Calibrate models:"
echo "   python3 scripts/calibrate_models.py"
echo ""
echo "4️⃣  Launch the dashboard:"
echo "   streamlit run app.py"
echo ""
echo "5️⃣  Or run data collection:"
echo "   python3 scripts/collect_data.py"
echo ""
echo "=================================================="
echo ""
print_info "Virtual environment is activated. To activate it later, run:"
echo "   source venv/bin/activate    (Linux/Mac)"
echo "   venv\\Scripts\\activate      (Windows)"
echo ""
print_info "To deactivate: deactivate"
echo ""
echo "📚 Documentation:"
echo "   - README.md - General overview"
echo "   - TRAINING_GUIDE.md - Model training guide"
echo "   - docs/DATA_SOURCES.md - Data sources"
echo ""
echo "Good luck! 🍀"
