@echo off
echo ===============================================
echo    GitHub Actions Repository Setup
echo ===============================================
echo.

echo This script will prepare your repository for GitHub Actions
echo which will automatically build and release your executable.
echo.

echo Step 1: Create Repository Structure
echo ----------------------------------

if not exist ".github" mkdir .github
if not exist ".github\workflows" mkdir .github\workflows

echo ✅ Created .github/workflows directory

echo.
echo Step 2: Copy Source Files for Upload
echo ------------------------------------

if not exist "src" mkdir src

echo Copying Python source files...
copy "osmosis_main.py" "src\" 2>nul
copy "ctvlist_gui.py" "src\" 2>nul
copy "pyuber_query.py" "src\" 2>nul
copy "smart_json_parser.py" "src\" 2>nul
copy "file_functions.py" "src\" 2>nul
copy "index_ctv.py" "src\" 2>nul
copy "mtpl_parser.py" "src\" 2>nul

echo ✅ Source files copied to src/ directory

echo.
echo Step 3: Verify Required Files
echo -----------------------------

set "missing_files="

if not exist "build_app.py" (
    echo ❌ build_app.py missing
    set "missing_files=1"
) else (
    echo ✅ build_app.py found
)

if not exist "requirements.txt" (
    echo ❌ requirements.txt missing
    set "missing_files=1"
) else (
    echo ✅ requirements.txt found
)

if not exist ".github\workflows\build-and-release.yml" (
    echo ❌ GitHub Actions workflow missing
    set "missing_files=1"
) else (
    echo ✅ GitHub Actions workflow found
)

if not exist "PyUber" (
    echo ❌ PyUber directory missing
    set "missing_files=1"
) else (
    echo ✅ PyUber directory found
)

if not exist "Uber" (
    echo ❌ Uber directory missing
    set "missing_files=1"
) else (
    echo ✅ Uber directory found
)

echo.
echo Step 4: Create .gitignore
echo -------------------------

echo # Python bytecode > .gitignore
echo __pycache__/ >> .gitignore
echo *.py[cod] >> .gitignore
echo *$py.class >> .gitignore
echo. >> .gitignore
echo # Distribution / packaging >> .gitignore
echo build/ >> .gitignore
echo dist/ >> .gitignore
echo *.egg-info/ >> .gitignore
echo. >> .gitignore
echo # IDE >> .gitignore
echo .vscode/ >> .gitignore
echo .idea/ >> .gitignore
echo *.swp >> .gitignore
echo *.swo >> .gitignore
echo. >> .gitignore
echo # OS >> .gitignore
echo .DS_Store >> .gitignore
echo Thumbs.db >> .gitignore
echo desktop.ini >> .gitignore
echo. >> .gitignore
echo # Logs >> .gitignore
echo *.log >> .gitignore
echo. >> .gitignore
echo # Large files (use Git LFS instead) >> .gitignore
echo *.zip >> .gitignore
echo *.exe >> .gitignore

echo ✅ .gitignore created

echo.
echo Step 5: Create README for GitHub
echo --------------------------------

if not exist "GITHUB_README.md" (
    echo ❌ GITHUB_README.md not found
    echo Create this file or rename an existing README
) else (
    copy "GITHUB_README.md" "README.md" >nul
    echo ✅ README.md created from GITHUB_README.md
)

echo.
echo ===============================================
echo               REPOSITORY STATUS
echo ===============================================

if defined missing_files (
    echo ❌ Some required files are missing
    echo Please ensure all files are in place before uploading
) else (
    echo ✅ All required files present
    echo Your repository is ready for GitHub Actions!
)

echo.
echo Next Steps:
echo 1. Initialize git repository: git init
echo 2. Add all files: git add .
echo 3. Commit: git commit -m "Initial commit with GitHub Actions"
echo 4. Create GitHub repository
echo 5. Push code: git remote add origin [your-repo-url]
echo 6. Push: git push -u origin main
echo 7. Create release: git tag v2.0.0 ^&^& git push origin v2.0.0
echo.

echo Files to upload to GitHub:
echo - All .py files in src/
echo - PyUber/ directory
echo - Uber/ directory  
echo - build_app.py
echo - requirements.txt
echo - .github/workflows/build-and-release.yml
echo - README.md
echo - .gitignore
echo.

echo DO NOT UPLOAD:
echo - dist/ directory
echo - __pycache__/ directories
echo - *.exe files
echo - Large ZIP files
echo.

echo ===============================================
echo GitHub will automatically build your executable!
echo Build time: ~10-15 minutes per release
echo ===============================================
pause
