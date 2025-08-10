# Create a complete file listing and prepare for zip creation
import os
import zipfile
from pathlib import Path

def get_file_tree(directory, prefix=""):
    """Generate a file tree representation"""
    items = []
    path = Path(directory)
    
    if not path.exists():
        return []
    
    # Get all items and sort them
    all_items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
    
    for item in all_items:
        if item.name.startswith('.') and item.name not in ['.env.template']:
            continue
            
        if item.is_dir():
            items.append(f"{prefix}📁 {item.name}/")
            # Recursively get subdirectory contents
            sub_items = get_file_tree(item, prefix + "  ")
            items.extend(sub_items)
        else:
            # Get file size
            try:
                size = item.stat().st_size
                size_str = f" ({size:,} bytes)" if size < 1024 else f" ({size/1024:.1f} KB)"
            except:
                size_str = ""
            items.append(f"{prefix}📄 {item.name}{size_str}")
    
    return items

# Generate file tree
print("📁 LC Validation System - Complete File Structure")
print("=" * 60)

file_tree = get_file_tree("lc_validation_system")
for item in file_tree:
    print(item)

print(f"\n📊 Summary Statistics:")
total_files = len([item for item in file_tree if item.strip().startswith("📄")])
total_dirs = len([item for item in file_tree if item.strip().startswith("📁")])
print(f"Total Files: {total_files}")
print(f"Total Directories: {total_dirs}")

# Create zip file
zip_filename = "lc_validation_system.zip"
print(f"\n📦 Creating zip package: {zip_filename}")

def create_zip_archive(source_dir, output_filename):
    """Create a zip archive of the source directory"""
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        source_path = Path(source_dir)
        
        for file_path in source_path.rglob('*'):
            if file_path.is_file():
                # Skip hidden files except .env.template
                if file_path.name.startswith('.') and file_path.name != '.env.template':
                    continue
                
                # Add file to zip
                arcname = file_path.relative_to(source_path.parent)
                zipf.write(file_path, arcname)
                
        return zipf.filename

try:
    zip_path = create_zip_archive("lc_validation_system", zip_filename)
    zip_size = Path(zip_filename).stat().st_size
    print(f"✅ Zip package created successfully!")
    print(f"📦 File: {zip_filename}")
    print(f"💾 Size: {zip_size/1024:.1f} KB")
    
except Exception as e:
    print(f"❌ Error creating zip: {str(e)}")

print("\n🎉 LC Validation System Package Complete!")
print("=" * 60)