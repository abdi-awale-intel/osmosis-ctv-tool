# GitHub Actions Quick Reference

## 🚀 How to Release New Versions

### Method 1: Create Release Tag (Recommended)
```bash
# Create and push a version tag
git tag v2.0.0
git push origin v2.0.0

# GitHub automatically:
# 1. Detects the tag
# 2. Runs the build workflow  
# 3. Creates executable
# 4. Publishes release with download
```

### Method 2: Create GitHub Release
1. Go to your repository on GitHub
2. Click "Releases" → "Create a new release"
3. Choose tag: `v2.0.0` (create new)
4. Release title: `Osmosis v2.0 - Complete with PyUber Integration`
5. Click "Publish release"
6. GitHub automatically builds and attaches executable

### Method 3: Manual Trigger
1. Go to "Actions" tab in your repository
2. Select "Build and Release Osmosis"  
3. Click "Run workflow"
4. Choose branch and click "Run workflow"

## 📦 What GitHub Builds

### Automatic Process:
1. **Setup** Python 3.11 environment
2. **Install** dependencies from requirements.txt
3. **Build** executable with PyInstaller
4. **Package** everything into ZIP
5. **Upload** as release asset

### Build Output:
- `Osmosis_v2.0_Complete.zip` (~50MB)
- Contains: executable, PyUber, Uber, installers
- Ready for direct download and use

## 🔄 Development Workflow

### For Code Changes:
```bash
# Make your changes
git add .
git commit -m "Add new feature"
git push

# When ready to release:
git tag v2.1.0
git push origin v2.1.0
# GitHub builds new version automatically
```

### For Quick Testing:
```bash
# Use manual trigger in GitHub Actions
# Or create pre-release versions:
git tag v2.0.0-beta
git push origin v2.0.0-beta
```

## 📊 Build Status

### Build Success:
- ✅ Green checkmark in Actions tab
- 📦 ZIP file attached to release
- 🔗 Download link available

### Build Failure:
- ❌ Red X in Actions tab  
- 📋 Check logs in Actions tab
- 🔧 Fix issues and push again

## 🎯 Download Links

### After Build Completes:
```
Direct Download:
https://github.com/[username]/osmosis-ctv-tool/releases/download/v2.0.0/Osmosis_v2.0_Complete.zip

Release Page:
https://github.com/[username]/osmosis-ctv-tool/releases/tag/v2.0.0

Latest Release:
https://github.com/[username]/osmosis-ctv-tool/releases/latest
```

## 🏗️ Build Environment

### GitHub Provides:
- Windows Server (latest)
- Python 3.11
- 2-core CPU, 7GB RAM  
- Build time: ~10-15 minutes
- Free for public repositories

### Build Steps:
1. **Checkout** (30 seconds)
2. **Setup Python** (1 minute)
3. **Install deps** (2-3 minutes)
4. **Build executable** (5-8 minutes)
5. **Package & upload** (1-2 minutes)

## 🛠️ Troubleshooting

### Build Fails:
- Check dependency issues in requirements.txt
- Verify PyUber imports work
- Check PyInstaller compatibility

### Large Build Time:
- Normal for PyInstaller + PyUber
- Consider caching pip dependencies
- Build time is one-time per release

### Missing Files:
- Ensure all source files are committed
- Check .gitignore doesn't exclude needed files
- Verify PyUber and Uber directories uploaded

## 🎉 Benefits

### ✅ Advantages:
- **No file size limits** - source code is small
- **Always fresh builds** - latest code
- **Automatic versioning** - based on tags
- **Build logs** - transparent process
- **Multiple platforms** - can add Linux/Mac
- **Professional CI/CD** - industry standard

### 📈 Usage:
1. Upload source code once
2. Create releases with git tags
3. GitHub builds automatically
4. Users download fresh executables
5. No manual packaging needed!

## 🔧 Advanced Options

### Build for Multiple OS:
```yaml
strategy:
  matrix:
    os: [windows-latest, ubuntu-latest, macos-latest]
```

### Scheduled Builds:
```yaml
on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly builds
```

### Custom Build Triggers:
```yaml
on:
  push:
    branches: [main]
    paths: ['src/**']  # Only on source changes
```

---

**Your users get the same experience - download and run - but you get automatic building! 🚀**
