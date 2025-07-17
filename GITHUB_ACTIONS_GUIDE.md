# GitHub Actions: Build & Release Automation

## 🚀 Upload Source Code → Auto-Build → Download Executable

Instead of uploading the 54MB package, upload your source code and let GitHub build it automatically!

## 🎯 How GitHub Actions Works

1. **Upload Source Code** (small files, no size limits)
2. **GitHub Actions Builds** your app automatically
3. **Creates Release** with downloadable executable
4. **Users Download** the built executable

## 📁 Repository Structure

```
osmosis-ctv-tool/
├── .github/
│   └── workflows/
│       └── build-and-release.yml    # Build automation
├── src/                             # Your source code
│   ├── osmosis_main.py
│   ├── ctvlist_gui.py
│   ├── pyuber_query.py
│   ├── smart_json_parser.py
│   ├── file_functions.py
│   ├── index_ctv.py
│   └── mtpl_parser.py
├── PyUber/                          # PyUber library source
├── Uber/                            # Uber configuration
├── resources/                       # Resources folder
├── requirements.txt                 # Python dependencies
├── build_app.py                     # Build script
├── README.md                        # Documentation
└── .gitignore                       # Git ignore file
```

## ⚙️ GitHub Actions Workflow

This will automatically build your app on every release:

```yaml
name: Build and Release Osmosis

on:
  push:
    tags:
      - 'v*'  # Triggers on version tags like v2.0.0
  release:
    types: [created]

jobs:
  build:
    runs-on: windows-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pyinstaller
        
    - name: Build executable
      run: |
        python build_app.py
        
    - name: Create distribution package
      run: |
        mkdir release_package
        xcopy /E /I dist release_package
        powershell -command "Compress-Archive -Path 'release_package\*' -DestinationPath 'Osmosis_v2.0_Complete.zip'"
        
    - name: Upload release asset
      uses: actions/upload-release-asset@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      with:
        upload_url: ${{ github.event.release.upload_url }}
        asset_path: ./Osmosis_v2.0_Complete.zip
        asset_name: Osmosis_v2.0_Complete.zip
        asset_content_type: application/zip
```

## 🔧 Setup Steps

### 1. Prepare Your Repository Structure
- Upload source code (not binaries)
- Include build scripts
- Add requirements.txt
- Create GitHub Actions workflow

### 2. Create Workflow File
Save the above YAML as `.github/workflows/build-and-release.yml`

### 3. Push and Tag
```bash
git add .
git commit -m "Add GitHub Actions build workflow"
git push

# Create a release tag
git tag v2.0.0
git push origin v2.0.0
```

### 4. GitHub Builds Automatically
- GitHub runs the build process
- Creates the executable
- Attaches it to the release
- Users can download the built package

## 🏆 Benefits of This Approach

### ✅ Advantages:
- **No file size limits** - source code is small
- **Automatic building** - no manual packaging
- **Version control** - full source history
- **Transparency** - users can see source code
- **CI/CD pipeline** - professional development
- **Multiple platforms** - can build for different OS
- **Always fresh** - builds latest code automatically

### 📊 Build Time:
- **Setup**: ~2 minutes (Python + dependencies)
- **Build**: ~5-10 minutes (PyInstaller + packaging)
- **Total**: ~12-15 minutes per release

## 📋 Files You Need to Upload

### Essential Source Files:
```
✅ All .py files (osmosis_main.py, ctvlist_gui.py, etc.)
✅ PyUber/ directory (source code, not compiled)
✅ Uber/ directory (configuration files)
✅ resources/ directory
✅ requirements.txt
✅ build_app.py
✅ .github/workflows/build-and-release.yml
❌ No dist/ folder needed
❌ No compiled .exe files
❌ No __pycache__ folders
```

### Requirements.txt Example:
```
tkinter
pandas
openpyxl
requests
pillow
pyinstaller
```

## 🎯 User Experience

### For Users:
1. Go to GitHub releases page
2. Download `Osmosis_v2.0_Complete.zip`
3. Extract and run - same as before!

### For You:
1. Make code changes
2. Push to GitHub
3. Create release tag
4. GitHub automatically builds and publishes!

## 🔄 Advanced Features

### Multiple OS Support:
```yaml
strategy:
  matrix:
    os: [windows-latest, ubuntu-latest, macos-latest]
runs-on: ${{ matrix.os }}
```

### Automatic Version Numbering:
```yaml
- name: Get version from tag
  run: echo "VERSION=${GITHUB_REF#refs/tags/}" >> $GITHUB_ENV
```

### Build Artifacts:
- Executables for different platforms
- Source code archives
- Debug symbols (if needed)

## 💡 Quick Start Script

I'll create a script to set up your repository structure for GitHub Actions automation.

Would you like me to:
1. **Create the GitHub Actions workflow file**
2. **Prepare your repository structure**
3. **Set up requirements.txt and build scripts**
4. **Create upload scripts for easy deployment**

This approach is much more professional and eliminates the 25MB file size issue completely!
