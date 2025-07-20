#!/usr/bin/env python3
"""
Migration helper for Osmosis CTV Tool
Helps update import statements after reorganization
"""

import os
import re
import sys
from pathlib import Path

def find_python_files(directory):
    """Find all Python files in directory"""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Skip build directories
        dirs[:] = [d for d in dirs if d not in ['build', 'dist', '__pycache__', '.git']]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    return python_files

def update_imports(file_path, dry_run=True):
    """Update import statements in a Python file"""
    
    # Module mappings (old import -> new import)
    module_mappings = {
        'osmosis_main': 'src.osmosis_main',
        'ctvlist_gui': 'src.ctvlist_gui', 
        'deploy_ctvlist': 'src.deploy_ctvlist',
        'pyuber_query': 'src.pyuber_query',
        'smart_json_parser': 'src.smart_json_parser',
        'file_functions': 'src.file_functions',
        'mtpl_parser': 'src.mtpl_parser',
        'index_ctv': 'src.index_ctv',
        'download_server': 'src.download_server',
        'build_app': 'src.build_app'
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return False
    
    original_content = content
    changes_made = []
    
    # Update import statements
    for old_module, new_module in module_mappings.items():
        # Pattern for "import module" 
        pattern1 = rf'\bimport\s+{re.escape(old_module)}\b'
        if re.search(pattern1, content):
            content = re.sub(pattern1, f'import {new_module}', content)
            changes_made.append(f"import {old_module} -> import {new_module}")
        
        # Pattern for "from module import ..."
        pattern2 = rf'\bfrom\s+{re.escape(old_module)}\s+import\b'
        if re.search(pattern2, content):
            content = re.sub(pattern2, f'from {new_module} import', content)
            changes_made.append(f"from {old_module} -> from {new_module}")
    
    if content != original_content:
        if not dry_run:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ Updated {file_path}")
                for change in changes_made:
                    print(f"   {change}")
            except Exception as e:
                print(f"❌ Error writing {file_path}: {e}")
                return False
        else:
            print(f"📝 Would update {file_path}")
            for change in changes_made:
                print(f"   {change}")
        return True
    else:
        return False

def main():
    """Main migration function"""
    print("🔄 Osmosis Import Migration Helper")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == '--apply':
        dry_run = False
        print("🚨 APPLYING CHANGES (not a dry run)")
    else:
        dry_run = True
        print("👀 DRY RUN MODE (use --apply to make changes)")
    
    print()
    
    # Find Python files
    current_dir = Path('.')
    python_files = find_python_files(current_dir)
    
    if not python_files:
        print("❌ No Python files found")
        return
    
    print(f"📁 Found {len(python_files)} Python files")
    print()
    
    # Update files
    updated_count = 0
    for file_path in python_files:
        # Skip files in src directory (they're the source)
        if 'src' in file_path.parts:
            continue
            
        if update_imports(file_path, dry_run):
            updated_count += 1
    
    print()
    print(f"📊 Summary: {updated_count} files {'updated' if not dry_run else 'would be updated'}")
    
    if dry_run and updated_count > 0:
        print()
        print("💡 To apply changes, run: python migrate_imports.py --apply")

if __name__ == "__main__":
    main()
