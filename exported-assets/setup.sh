#!/bin/bash
# LC Validation System Setup Script

echo "🏦 LC Validation System Setup"
echo "============================="

# Check Python version
echo "Checking Python version..."
python --version

# Create virtual environment (optional but recommended)
echo "Creating virtual environment..."
python -m venv lc_validation_env
source lc_validation_env/bin/activate  # On Windows: lc_validation_env\Scripts\activate

# Install requirements
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Setup data
echo "Setting up data directory..."
python init_data.py

echo ""
echo "✅ Setup completed!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your OpenAI API key"
echo "2. Place UCP600 and ISBP745 PDF files in the data/ directory"
echo "3. Run: python main.py"
echo ""
echo "For more information, see README.md"
