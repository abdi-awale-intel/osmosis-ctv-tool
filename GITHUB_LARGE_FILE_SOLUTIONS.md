# GitHub Large File Solutions for Osmosis v2.0

## 🚨 Problem: File Too Large (54MB > 25MB GitHub Limit)

Your `Osmosis_v2.0_Complete.zip` is 54MB, but GitHub has a 25MB limit for regular files.

## 🎯 Solution Options

### Option 1: Git LFS (Large File Storage) - RECOMMENDED
Git LFS allows files up to 2GB on GitHub.

#### Setup Steps:
1. **Install Git LFS** (if not already installed)
   ```bash
   git lfs install
   ```

2. **Track large files**
   ```bash
   git lfs track "*.zip"
   git add .gitattributes
   ```

3. **Add and commit**
   ```bash
   git add Osmosis_v2.0_Complete.zip
   git commit -m "Add Osmosis v2.0 complete package"
   git push
   ```

4. **Create release as normal**
   - GitHub will handle the LFS file automatically
   - Download link will work normally for users

### Option 2: Split the Package
Split your 54MB package into smaller parts.

#### Create Split Package:
```bash
# Split into 20MB chunks
7z a -v20m Osmosis_v2.0_Part.7z Osmosis_v2.0_Complete.zip
```

This creates:
- `Osmosis_v2.0_Part.7z.001` (~20MB)
- `Osmosis_v2.0_Part.7z.002` (~20MB)  
- `Osmosis_v2.0_Part.7z.003` (~14MB)

#### User Instructions:
1. Download all parts
2. Use 7-Zip to extract: "Extract Here" on .001 file
3. Original ZIP is recreated

### Option 3: Alternative Download Hosts

#### OneDrive/SharePoint (Intel)
```
https://intel-my.sharepoint.com/personal/[username]/Documents/Osmosis_v2.0_Complete.zip
```

#### Google Drive
```
https://drive.google.com/file/d/[FILE_ID]/view?usp=sharing
```

#### Dropbox
```
https://www.dropbox.com/s/[SHARE_KEY]/Osmosis_v2.0_Complete.zip?dl=1
```

### Option 4: Optimize Package Size
Reduce the package size by removing unnecessary files.

#### Potential Reductions:
- Remove debug symbols from executables
- Compress PyUber libraries further  
- Exclude unnecessary Uber test files
- Use UPX to compress the main executable

## 🏆 RECOMMENDED APPROACH: Git LFS

### Why Git LFS is Best:
✅ **Native GitHub integration**
✅ **Handles large files seamlessly**  
✅ **No user complexity**
✅ **Professional solution**
✅ **Version tracking for large files**

### Git LFS Setup Script:
```bash
# Navigate to your repository
cd /path/to/your/repo

# Install and setup LFS
git lfs install
git lfs track "*.zip"
git lfs track "*.exe"

# Add the tracking file
git add .gitattributes

# Add your large file
git add Osmosis_v2.0_Complete.zip

# Commit and push
git commit -m "Add Osmosis v2.0 with Git LFS"
git push origin main

# Create release as usual
```

## 📋 Updated GitHub Workflow

### With Git LFS:
1. **Setup Repository** with Git LFS enabled
2. **Upload large file** via Git LFS tracking
3. **Create release** normally - GitHub handles LFS automatically
4. **Users download** normally - no difference for them

### Download Link (same as before):
```
https://github.com/[username]/osmosis-ctv-tool/releases/download/v2.0.0/Osmosis_v2.0_Complete.zip
```

## 🔧 Alternative: Reduce Package Size

If you want to stay under 25MB, we can optimize:

### Potential Optimizations:
1. **UPX Compression** on executable (~30% reduction)
2. **Remove debug files** from PyUber
3. **Compress Uber configs** 
4. **Exclude test/example files**

Target: Get from 54MB → 20MB

## 💡 Quick Decision Guide

- **For simplicity:** Use Git LFS (recommended)
- **For compatibility:** Split into parts
- **For optimization:** Reduce package size
- **For convenience:** External hosting (OneDrive/Google Drive)

**Git LFS is the most professional solution and works seamlessly with GitHub releases!**
