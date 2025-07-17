@echo off
echo ===============================================
echo      Git LFS Setup for Large Osmosis Package
echo ===============================================
echo.

echo Current package size: ~54MB
echo GitHub limit: 25MB
echo Solution: Git Large File Storage (LFS)
echo.

echo Step 1: Install Git LFS
echo -----------------------
echo Download and install Git LFS from:
echo https://git-lfs.github.io/
echo.
echo Or if you have Git for Windows:
echo git lfs install
echo.

echo Step 2: Initialize Repository
echo -----------------------------
echo cd your-repository-folder
echo git init
echo git lfs install
echo.

echo Step 3: Track Large Files
echo -------------------------
echo git lfs track "*.zip"
echo git lfs track "*.exe"
echo git add .gitattributes
echo.

echo Step 4: Add Your Package
echo ------------------------
echo git add Osmosis_v2.0_Complete.zip
echo git add README.md
echo git commit -m "Initial release - Osmosis v2.0 with PyUber integration"
echo.

echo Step 5: Create GitHub Repository
echo --------------------------------
echo 1. Go to https://github.com/new
echo 2. Repository name: osmosis-ctv-tool
echo 3. Don't initialize with README (you already have one)
echo 4. Create repository
echo.

echo Step 6: Push to GitHub
echo ----------------------
echo git remote add origin https://github.com/[YOUR-USERNAME]/osmosis-ctv-tool.git
echo git branch -M main
echo git push -u origin main
echo.

echo Step 7: Create Release
echo ----------------------
echo 1. Go to your repository on GitHub
echo 2. Click "Releases" → "Create a new release"
echo 3. Tag: v2.0.0
echo 4. Title: Osmosis v2.0 - Complete with PyUber Integration
echo 5. Attach the ZIP file (GitHub will handle LFS automatically)
echo 6. Publish release
echo.

echo ===============================================
echo Your download link will be:
echo https://github.com/[USERNAME]/osmosis-ctv-tool/releases/download/v2.0.0/Osmosis_v2.0_Complete.zip
echo ===============================================
echo.

echo NOTE: Users won't notice any difference!
echo GitHub LFS makes large file downloads seamless.
echo.
pause
