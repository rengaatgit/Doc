@echo off
REM LC Validation System Setup Script for Windows

echo 🏦 LC Validation System Setup
echo =============================

REM Check Python version
echo Checking Python version...
python --version

REM Create virtual environment
echo Creating virtual environment...
python -m venv lc_validation_env
call lc_validation_env\Scripts\activate

REM Install requirements
echo Installing Python dependencies...
pip install -r requirements.txt

REM Setup data
echo Setting up data directory...
python init_data.py

echo.
echo ✅ Setup completed!
echo.
echo Next steps:
echo 1. Edit .env file and add your OpenAI API key
echo 2. Place UCP600 and ISBP745 PDF files in the data/ directory  
echo 3. Run: python main.py
echo.
echo For more information, see README.md
pause
