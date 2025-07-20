# 🚀 Osmosis Build System - Quick Reference

## 🔧 Available Build Methods

### 1. Python Build Script (Recommended)
```bash
python build.py [command]
```

### 2. PowerShell Build Script  
```powershell
.\build.ps1 [command]
```

### 3. Legacy Batch File
```cmd
build.bat [command]
```

## 📋 Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `clean` | Clean build artifacts | `python build.py clean` |
| `deps` | Install dependencies | `python build.py deps` |
| `wheel` | Build Python wheel package | `python build.py wheel` |
| `exe` | Build standalone executable | `python build.py exe` |
| `package` | Create distribution package | `python build.py package` |
| `test` | Run tests if available | `python build.py test` |
| `version X.Y` | Update version number | `python build.py version 2.1` |
| `full` | Complete build process | `python build.py full` |

## 🎯 Common Workflows

### Quick Development Build
```bash
python build.py clean
python build.py exe
```

### Release Build
```bash
python build.py version 2.1.0
python build.py full
```

### Package Only
```bash
python build.py package
```

## 📁 Output Locations

- **Executable**: `dist/Osmosis/Osmosis.exe`
- **Wheel Package**: `dist/*.whl` 
- **Distribution**: `package_output/Osmosis_v{version}_Complete.zip`
- **Build Logs**: Console output

## 🔄 Git-like Workflow

The new structure follows modern Python/Git repository conventions:

```
📁 osmosis-ctv-tool/
├── 📁 src/           # Source code (like 'src' in Git repos)
├── 🏗️ build.py       # Build system
├── ⚙️ setup.py       # Python packaging
├── 📋 requirements.txt
└── 📦 package_output/ # Distribution files
```

## 🚨 Migration Notes

### Old vs New
- **Old**: Root-level Python files 
- **New**: Organized in `src/` directory
- **Old**: Manual batch files
- **New**: Automated build system with multiple interfaces

### Breaking Changes
- Python files moved to `src/` directory
- Build process updated for modern packaging
- Import paths may need updates in custom scripts

## 🛠️ Troubleshooting

### Common Issues
1. **Import Errors**: Update import paths to use `src.module_name`
2. **Missing Dependencies**: Run `python build.py deps`
3. **Permission Errors**: Run as Administrator for installation
4. **PowerShell Execution Policy**: Use `Set-ExecutionPolicy RemoteSigned`

### Quick Fixes
```bash
# Reset and rebuild
python build.py clean
python build.py full

# Install missing packages
pip install -r requirements.txt

# Check Python environment
python --version
pip list
```

---
**Last Updated**: July 20, 2025  
**Version**: 2.0.1+
