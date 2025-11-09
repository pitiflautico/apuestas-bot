@echo off
REM Auto-installer for Sports Props Bot (Windows)

echo ========================================
echo Sports Props Intelligence Bot - Windows Installer
echo ========================================
echo.

REM Check for Python 3
echo Checking for Python 3...

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found!
    echo Please install Python 3.10+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found Python %PYTHON_VERSION%

REM Check version is 3.10+
python -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python version too old: %PYTHON_VERSION%
    echo Requires Python 3.10 or higher
    pause
    exit /b 1
)

echo [OK] Python version check passed
echo.

REM Check for pip
echo Checking for pip...
python -m pip --version >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] pip not found! Installing...
    python -m ensurepip --upgrade
)

echo [OK] pip found
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Create virtual environment
echo Creating virtual environment...

if exist "venv\" (
    echo Virtual environment already exists
    set /p "RECREATE=Do you want to recreate it? (y/N): "
    if /i "%RECREATE%"=="y" (
        rmdir /s /q venv
        python -m venv venv
        echo [OK] Virtual environment recreated
    )
) else (
    python -m venv venv
    echo [OK] Virtual environment created
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo [OK] Virtual environment activated
echo.

REM Install dependencies
echo Installing core dependencies...
echo This may take a few minutes...
echo.

pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo.
echo [OK] All dependencies installed!
echo.

REM Ask about ML libraries
set /p "INSTALL_ML=Do you want to install optional ML libraries (XGBoost, LightGBM)? (y/N): "
if /i "%INSTALL_ML%"=="y" (
    echo Installing ML libraries...
    pip install xgboost lightgbm
    echo [OK] ML libraries installed
) else (
    echo [INFO] Skipped ML libraries
)
echo.

REM Create directories
echo Creating data directories...

if not exist "data\raw\nba" mkdir data\raw\nba
if not exist "data\raw\acb" mkdir data\raw\acb
if not exist "data\raw\laliga" mkdir data\raw\laliga
if not exist "data\raw\tennis" mkdir data\raw\tennis
if not exist "data\curated" mkdir data\curated
if not exist "data\results" mkdir data\results
if not exist "data\models" mkdir data\models
if not exist "logs" mkdir logs
if not exist "docs" mkdir docs

echo [OK] Directories created
echo.

REM Setup .env file
echo Setting up environment file...

if exist ".env" (
    echo .env file already exists
    set /p "OVERWRITE=Do you want to overwrite it? (y/N): "
    if /i "%OVERWRITE%"=="y" (
        copy /y .env.example .env
        echo [OK] .env file created from template
    )
) else (
    copy .env.example .env
    echo [OK] .env file created from template
)
echo.

REM Initialize database
echo Initializing database...

python -c "import sys; sys.path.insert(0, 'src'); from database import init_db; init_db(); print('[OK] Database initialized')"
echo.

REM Verify installation
echo Verifying installation...
echo.

python -c "import sys; print(f'Python: {sys.version}'); import pandas; print(f'[OK] pandas {pandas.__version__}'); import numpy; print(f'[OK] numpy {numpy.__version__}'); import streamlit; print(f'[OK] streamlit {streamlit.__version__}'); import sqlalchemy; print(f'[OK] sqlalchemy {sqlalchemy.__version__}')"

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Next Steps:
echo.
echo 1. Edit .env file with your API keys:
echo    notepad .env
echo.
echo 2. Download historical data:
echo    python scripts\populate_historical_data.py --quick
echo.
echo 3. Calibrate models:
echo    python scripts\calibrate_models.py
echo.
echo 4. Launch the dashboard:
echo    streamlit run app.py
echo.
echo ========================================
echo.
echo To activate virtual environment later:
echo    venv\Scripts\activate.bat
echo.
echo To deactivate: deactivate
echo.
echo Good luck!
echo.
pause
