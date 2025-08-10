
"""
Data Initialization Script
Prepares the data for the LC validation system
"""

import os
import shutil
from pathlib import Path
import pandas as pd


def setup_data_directory():
    """Setup data directory and copy files"""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    print("📁 Setting up data directory...")

    # Copy attached files to data directory
    files_to_copy = {
        "isbp-745.pdf": "data/isbp-745.pdf",
        "UCP600-1.pdf": "data/UCP600-1.pdf", 
        "mappings.xlsx": "data/mappings.xlsx",
        "sampleLC.txt": "sampleLC.txt"
    }

    for source, dest in files_to_copy.items():
        if Path(source).exists():
            shutil.copy(source, dest)
            print(f"✅ Copied {source} to {dest}")
        else:
            print(f"⚠️  {source} not found")

    print("✅ Data directory setup completed!")


def verify_mappings():
    """Verify mappings data structure"""
    mappings_path = "data/mappings.xlsx"
    if Path(mappings_path).exists():
        try:
            df = pd.read_excel(mappings_path, sheet_name=0)
            print(f"📊 Mappings loaded: {len(df)} rows")

            # Check required columns
            required_cols = ["LC Section", "UCP600 Article", "ISBP745 Section", "Remarks"]
            missing_cols = [col for col in required_cols if col not in df.columns]

            if missing_cols:
                print(f"⚠️  Missing columns in mappings: {missing_cols}")
            else:
                print("✅ Mappings structure verified")

            return True
        except Exception as e:
            print(f"❌ Error loading mappings: {str(e)}")
            return False
    return False


def create_env_file():
    """Create environment file from template"""
    if not Path(".env").exists() and Path(".env.template").exists():
        shutil.copy(".env.template", ".env")
        print("📝 Created .env file from template")
        print("⚠️  Please update .env file with your OpenAI API key")
    else:
        print("ℹ️  .env file already exists or template not found")


def main():
    """Main initialization function"""
    print("🚀 Initializing LC Validation System Data")
    print("=" * 50)

    setup_data_directory()
    verify_mappings()
    create_env_file()

    print("\n✅ Data initialization completed!")
    print("\nNext steps:")
    print("1. Update .env file with your OpenAI API key")
    print("2. Run: pip install -r requirements.txt")
    print("3. Run: python main.py")


if __name__ == "__main__":
    main()
