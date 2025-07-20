#!/usr/bin/env python3
"""
Modern build script for Osmosis CTV Tool
Replaces old batch files with Python-based build system
"""

import os
import sys
import shutil
import subprocess
import json
from pathlib import Path
from datetime import datetime

class OsmosisBuildSystem:
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.src_dir = self.root_dir / "src"
        self.build_dir = self.root_dir / "build"
        self.dist_dir = self.root_dir / "dist"
        self.package_dir = self.root_dir / "package_output"
        
        # Load config
        with open(self.root_dir / "config.json", 'r') as f:
            self.config = json.load(f)
        
        self.version = self.config['application']['version']
        self.app_name = self.config['application']['name']
        
    def clean(self):
        """Clean build artifacts"""
        print("🧹 Cleaning build artifacts...")
        
        dirs_to_clean = [self.build_dir, self.dist_dir, self.package_dir / "temp"]
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"   Removed: {dir_path}")
        
        # Clean pycache
        for pycache in self.root_dir.rglob("__pycache__"):
            shutil.rmtree(pycache)
            print(f"   Removed: {pycache}")
            
        print("✅ Clean complete!")
    
    def install_deps(self):
        """Install dependencies"""
        print("📦 Installing dependencies...")
        
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ], check=True, cwd=self.root_dir)
            
            # Install build dependencies
            subprocess.run([
                sys.executable, "-m", "pip", "install", 
                "pyinstaller>=4.5", "setuptools>=45.0", "wheel>=0.35"
            ], check=True)
            
            print("✅ Dependencies installed!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            sys.exit(1)
    
    def build_wheel(self):
        """Build Python wheel package"""
        print("🏗️ Building wheel package...")
        
        try:
            subprocess.run([
                sys.executable, "setup.py", "bdist_wheel"
            ], check=True, cwd=self.root_dir)
            
            print("✅ Wheel package built!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to build wheel: {e}")
            sys.exit(1)
    
    def build_executable(self):
        """Build standalone executable with PyInstaller"""
        print("🔨 Building standalone executable...")
        
        try:
            subprocess.run([
                sys.executable, "-m", "PyInstaller", 
                "--clean", "--noconfirm", "osmosis.spec"
            ], check=True, cwd=self.root_dir)
            
            print("✅ Executable built!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to build executable: {e}")
            sys.exit(1)
    
    def create_package(self):
        """Create distribution package"""
        print("📦 Creating distribution package...")
        
        # Create package structure
        package_name = f"Osmosis_v{self.version}_Complete"
        package_path = self.package_dir / package_name
        
        if package_path.exists():
            shutil.rmtree(package_path)
        
        package_path.mkdir(parents=True, exist_ok=True)
        
        # Copy executable
        exe_source = self.dist_dir / "Osmosis" / "Osmosis.exe"
        if exe_source.exists():
            print(f"   Copying executable: {exe_source.stat().st_size / (1024*1024):.1f} MB")
            shutil.copy2(exe_source, package_path / "Osmosis.exe")
        else:
            print("   ⚠️ Executable not found, run 'build.py exe' first")
        
        # Copy supporting files
        support_files = [
            ("config.json", "config.json"),
            ("README.md", "README.md"),
            ("core_package/Install_Osmosis.bat", "Install_Osmosis.bat"),
            ("core_package/Install_Osmosis.ps1", "Install_Osmosis.ps1")
        ]
        
        for src_path, dst_name in support_files:
            source = self.root_dir / src_path
            if source.exists():
                shutil.copy2(source, package_path / dst_name)
                print(f"   Copied: {dst_name}")
        
        # Copy directories (only essential ones for faster install)
        dir_copies = [
            ("PyUber", "PyUber"),
            ("resources", "resources"),
            ("Uber", "Uber")
        ]
        
        total_size = 0
        for src_name, dst_name in dir_copies:
            src_path = self.root_dir / src_name
            if src_path.exists():
                dst_path = package_path / dst_name
                shutil.copytree(src_path, dst_path)
                
                # Calculate size
                dir_size = sum(f.stat().st_size for f in dst_path.rglob('*') if f.is_file())
                total_size += dir_size
                print(f"   Copied: {dst_name} ({dir_size / (1024*1024):.1f} MB)")
            else:
                print(f"   Skipped: {dst_name} (not found)")
        
        # Create optimized ZIP archive with compression
        zip_path = self.package_dir / f"{package_name}.zip"
        print(f"   Creating compressed archive...")
        shutil.make_archive(str(zip_path.with_suffix('')), 'zip', package_path)
        
        # Calculate compression ratio
        zip_size = zip_path.stat().st_size
        uncompressed_size = sum(f.stat().st_size for f in package_path.rglob('*') if f.is_file())
        compression_ratio = (1 - zip_size / uncompressed_size) * 100
        
        print(f"✅ Package created: {zip_path}")
        print(f"   Uncompressed: {uncompressed_size / (1024*1024):.1f} MB")
        print(f"   Compressed: {zip_size / (1024*1024):.1f} MB")
        print(f"   Compression: {compression_ratio:.1f}%")
        print(f"📁 Package folder: {package_path}")
    
    def update_version(self, new_version):
        """Update version in config"""
        print(f"🔢 Updating version to {new_version}...")
        
        self.config['application']['version'] = new_version
        self.config['application']['build_date'] = datetime.now().isoformat()
        
        with open(self.root_dir / "config.json", 'w') as f:
            json.dump(self.config, f, indent=4)
        
        print("✅ Version updated!")
    
    def run_tests(self):
        """Run tests if they exist"""
        test_dir = self.root_dir / "tests"
        if test_dir.exists():
            print("🧪 Running tests...")
            try:
                subprocess.run([
                    sys.executable, "-m", "pytest", str(test_dir)
                ], check=True, cwd=self.root_dir)
                print("✅ Tests passed!")
            except subprocess.CalledProcessError as e:
                print(f"❌ Tests failed: {e}")
                return False
        else:
            print("ℹ️ No tests found, skipping...")
        return True

def main():
    """Main build script entry point"""
    build_system = OsmosisBuildSystem()
    
    if len(sys.argv) < 2:
        print("🔧 Osmosis Build System")
        print("Usage: python build.py [command]")
        print("")
        print("Commands:")
        print("  clean       - Clean build artifacts")
        print("  deps        - Install dependencies")
        print("  wheel       - Build wheel package")
        print("  exe         - Build standalone executable")
        print("  package     - Create complete distribution package")
        print("  full        - Full build (clean + deps + exe + package)")
        print("  test        - Run tests")
        print("  version X.Y - Update version number")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "clean":
        build_system.clean()
    elif command == "deps":
        build_system.install_deps()
    elif command == "wheel":
        build_system.build_wheel()
    elif command == "exe":
        build_system.build_executable()
    elif command == "package":
        build_system.create_package()
    elif command == "test":
        build_system.run_tests()
    elif command == "version" and len(sys.argv) > 2:
        build_system.update_version(sys.argv[2])
    elif command == "full":
        print("🚀 Starting full build process...")
        build_system.clean()
        build_system.install_deps()
        if build_system.run_tests():
            build_system.build_executable()
            build_system.create_package()
            print("🎉 Full build completed successfully!")
        else:
            print("❌ Build stopped due to test failures")
            sys.exit(1)
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
