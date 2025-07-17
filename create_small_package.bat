@echo off
echo ===============================================
echo    Create Smaller Package for GitHub Upload
echo ===============================================
echo.

echo Current package: Osmosis_v2.0_Complete.zip (54MB)
echo GitHub limit: 25MB
echo.

echo Option 1: Split Package
echo ----------------------
echo We'll create multiple smaller files:
echo.

if exist "7z.exe" (
    echo Creating split archive...
    7z a -v20m Osmosis_v2.0_Split.7z dist\*
    echo.
    echo Created files:
    dir Osmosis_v2.0_Split.7z.*
    echo.
    echo Upload all .7z.001, .7z.002, .7z.003 files to GitHub
    echo Users download all parts and extract .001 with 7-Zip
) else (
    echo 7-Zip not found. Install from https://www.7-zip.org/
    echo Then run this script again.
)

echo.
echo Option 2: Create Core Package (Under 25MB)
echo ------------------------------------------

if not exist "core_package" mkdir core_package

echo Copying essential files only...
copy "dist\Osmosis.exe" "core_package\"
copy "dist\config.json" "core_package\"
copy "dist\Install_Osmosis.bat" "core_package\"
copy "dist\Launch_Osmosis.bat" "core_package\"
copy "README.md" "core_package\"

echo.
echo Creating core package...
powershell -command "Compress-Archive -Path 'core_package\*' -DestinationPath 'Osmosis_v2.0_Core.zip' -Force"

echo.
echo Checking size...
for %%I in (Osmosis_v2.0_Core.zip) do echo Core package size: %%~zI bytes

echo.
echo Option 3: External Download Link
echo --------------------------------
echo Upload complete package to:
echo - OneDrive/SharePoint (Intel)
echo - Google Drive
echo - Dropbox
echo.
echo Then reference download link in GitHub README
echo.

echo ===============================================
echo Choose your approach:
echo 1. Use Git LFS (recommended) - run setup_git_lfs.bat
echo 2. Upload split files created above
echo 3. Upload core package + external link for full version
echo 4. Use external hosting service
echo ===============================================
pause
