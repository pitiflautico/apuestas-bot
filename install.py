#!/usr/bin/env python3
"""
Python-based installer for Sports Props Bot
Works on all platforms (Linux, Mac, Windows)
"""

import sys
import os
import subprocess
import platform
from pathlib import Path


class Colors:
    """ANSI color codes"""
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


def print_success(msg):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {msg}{Colors.NC}")


def print_error(msg):
    """Print error message"""
    print(f"{Colors.RED}❌ {msg}{Colors.NC}")


def print_info(msg):
    """Print info message"""
    print(f"{Colors.YELLOW}ℹ️  {msg}{Colors.NC}")


def print_header(msg):
    """Print header"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"{msg}")
    print(f"{'='*60}{Colors.NC}\n")


def check_python_version():
    """Check if Python version is >= 3.10"""
    print("🔍 Checking Python version...")

    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    print(f"   Python {version_str} detected")

    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print_error(f"Python {version_str} is too old")
        print("   Please install Python 3.10 or higher")
        print("   Download from: https://www.python.org/")
        return False

    print_success(f"Python version OK: {version_str}")
    return True


def check_pip():
    """Check if pip is available"""
    print("\n🔍 Checking pip...")

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            check=True,
            capture_output=True
        )
        print_success("pip found")
        return True
    except subprocess.CalledProcessError:
        print_error("pip not found")
        print("   Installing pip...")
        try:
            subprocess.run(
                [sys.executable, "-m", "ensurepip", "--upgrade"],
                check=True
            )
            print_success("pip installed")
            return True
        except subprocess.CalledProcessError:
            print_error("Failed to install pip")
            return False


def upgrade_pip():
    """Upgrade pip to latest version"""
    print("\n📦 Upgrading pip...")

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            capture_output=True
        )
        print_success("pip upgraded")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to upgrade pip: {e}")
        return False


def create_venv():
    """Create virtual environment"""
    print("\n🌍 Creating virtual environment...")

    venv_path = Path("venv")

    if venv_path.exists():
        print_info("Virtual environment already exists")
        response = input("   Recreate it? (y/N): ").lower()

        if response == 'y':
            import shutil
            shutil.rmtree(venv_path)
            subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
            print_success("Virtual environment recreated")
        else:
            print_info("Using existing virtual environment")
    else:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print_success("Virtual environment created")

    return True


def get_venv_python():
    """Get path to Python in virtual environment"""
    if platform.system() == "Windows":
        return Path("venv") / "Scripts" / "python.exe"
    else:
        return Path("venv") / "bin" / "python"


def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing dependencies...")
    print("   This may take a few minutes...\n")

    venv_python = get_venv_python()

    # Upgrade pip in venv
    subprocess.run(
        [str(venv_python), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"],
        check=True
    )

    # Install requirements
    subprocess.run(
        [str(venv_python), "-m", "pip", "install", "-r", "requirements.txt"],
        check=True
    )

    print_success("Core dependencies installed")

    # Ask about ML libraries
    response = input("\n   Install optional ML libraries (XGBoost, LightGBM)? (y/N): ").lower()

    if response == 'y':
        print("   Installing ML libraries...")
        subprocess.run(
            [str(venv_python), "-m", "pip", "install", "xgboost", "lightgbm"],
            check=True
        )
        print_success("ML libraries installed")
    else:
        print_info("Skipped ML libraries")

    return True


def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")

    directories = [
        "data/raw/nba",
        "data/raw/acb",
        "data/raw/laliga",
        "data/raw/tennis",
        "data/curated",
        "data/results",
        "data/models",
        "logs",
        "docs"
    ]

    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

    print_success("Directories created")
    return True


def setup_env_file():
    """Setup .env file"""
    print("\n⚙️ Setting up environment file...")

    env_path = Path(".env")
    env_example = Path(".env.example")

    if env_path.exists():
        print_info(".env file already exists")
        response = input("   Overwrite it? (y/N): ").lower()

        if response == 'y':
            import shutil
            shutil.copy(env_example, env_path)
            print_success(".env file created from template")
    else:
        import shutil
        shutil.copy(env_example, env_path)
        print_success(".env file created from template")

    return True


def initialize_database():
    """Initialize database"""
    print("\n🗄️ Initializing database...")

    venv_python = get_venv_python()

    try:
        subprocess.run(
            [
                str(venv_python), "-c",
                "import sys; sys.path.insert(0, 'src'); from database import init_db; init_db(); print('OK')"
            ],
            check=True,
            capture_output=True
        )
        print_success("Database initialized")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Database initialization failed: {e}")
        return False


def verify_installation():
    """Verify installation"""
    print("\n🔍 Verifying installation...\n")

    venv_python = get_venv_python()

    verification_script = """
import sys
print(f'Python: {sys.version}')

packages = [
    'pandas', 'numpy', 'streamlit', 'sqlalchemy', 'scipy',
    'plotly', 'requests', 'beautifulsoup4'
]

for package in packages:
    try:
        mod = __import__(package)
        version = getattr(mod, '__version__', 'unknown')
        print(f'✅ {package} {version}')
    except ImportError:
        print(f'❌ {package} not installed')

# Optional packages
optional = ['xgboost', 'lightgbm']
for package in optional:
    try:
        mod = __import__(package)
        version = getattr(mod, '__version__', 'unknown')
        print(f'✅ {package} {version} (optional)')
    except ImportError:
        print(f'ℹ️  {package} not installed (optional)')
"""

    subprocess.run([str(venv_python), "-c", verification_script])


def print_next_steps():
    """Print next steps"""
    print_header("Installation Complete! 🎉")

    print("📋 Next Steps:\n")

    print("1️⃣  Edit .env file with your API keys:")
    print("   nano .env   (Linux/Mac)")
    print("   notepad .env   (Windows)\n")

    print("2️⃣  Activate virtual environment:")
    if platform.system() == "Windows":
        print("   venv\\Scripts\\activate\n")
    else:
        print("   source venv/bin/activate\n")

    print("3️⃣  Download historical data (optional):")
    print("   python scripts/populate_historical_data.py --quick\n")

    print("4️⃣  Calibrate models:")
    print("   python scripts/calibrate_models.py\n")

    print("5️⃣  Launch the dashboard:")
    print("   streamlit run app.py\n")

    print("="*60)
    print("\n📚 Documentation:")
    print("   - README.md - General overview")
    print("   - TRAINING_GUIDE.md - Model training")
    print("   - docs/DATA_SOURCES.md - Data sources\n")

    print("Good luck! 🍀\n")


def main():
    """Main installer function"""
    print_header("Sports Props Intelligence Bot - Installer")

    print(f"Platform: {platform.system()}")
    print(f"Architecture: {platform.machine()}\n")

    # Check Python version
    if not check_python_version():
        sys.exit(1)

    # Check pip
    if not check_pip():
        sys.exit(1)

    # Upgrade pip
    upgrade_pip()

    # Create virtual environment
    if not create_venv():
        sys.exit(1)

    # Install dependencies
    if not install_dependencies():
        sys.exit(1)

    # Create directories
    create_directories()

    # Setup .env
    setup_env_file()

    # Initialize database
    initialize_database()

    # Verify installation
    verify_installation()

    # Print next steps
    print_next_steps()


if __name__ == "__main__":
    main()
