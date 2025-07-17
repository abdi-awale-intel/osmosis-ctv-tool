@echo off
echo ===============================================
echo    OSMOSIS v2.0 - Package Builder
echo ===============================================
echo.

REM Set variables
set PACKAGE_NAME=Osmosis_v2.0_Complete
set BUILD_DIR=%~dp0
set DIST_DIR=%BUILD_DIR%dist
set PACKAGE_DIR=%BUILD_DIR%package_output

echo [INFO] Starting package creation...
echo [INFO] Build directory: %BUILD_DIR%
echo [INFO] Distribution directory: %DIST_DIR%
echo.

REM Check if dist folder exists
if not exist "%DIST_DIR%" (
    echo [ERROR] Distribution folder not found!
    echo [ERROR] Please run build_app.py first to create the distribution.
    pause
    exit /b 1
)

REM Create package output directory
if exist "%PACKAGE_DIR%" (
    echo [INFO] Cleaning previous package...
    rmdir /s /q "%PACKAGE_DIR%"
)
mkdir "%PACKAGE_DIR%"

REM Copy all distribution files
echo [INFO] Copying distribution files...
xcopy "%DIST_DIR%" "%PACKAGE_DIR%\%PACKAGE_NAME%\" /E /I /H /Y > nul

REM Copy additional deployment files
echo [INFO] Adding deployment files...
copy "%BUILD_DIR%osmosis_download.html" "%PACKAGE_DIR%\" > nul
copy "%BUILD_DIR%PYUBER_INTEGRATION_COMPLETE.md" "%PACKAGE_DIR%\" > nul

REM Create ZIP package
echo [INFO] Creating ZIP package...
cd /d "%PACKAGE_DIR%"

REM Use PowerShell to create ZIP file
powershell -Command "Compress-Archive -Path '%PACKAGE_NAME%' -DestinationPath '%PACKAGE_NAME%.zip' -Force"

if exist "%PACKAGE_NAME%.zip" (
    echo [SUCCESS] Package created successfully!
    echo [SUCCESS] Location: %PACKAGE_DIR%\%PACKAGE_NAME%.zip
    echo [SUCCESS] Size: 
    for %%A in ("%PACKAGE_NAME%.zip") do echo           %%~zA bytes
    echo.
    echo [INFO] Package contents:
    echo         - Osmosis.exe (Main application)
    echo         - PyUber/ (Database library)
    echo         - Uber/ (Configuration files)
    echo         - Install_Osmosis.bat (Installer)
    echo         - Documentation and resources
    echo.
    echo [INFO] Ready for distribution!
    
    REM Ask if user wants to open package location
    set /p OPEN_FOLDER="Open package folder? (Y/N): "
    if /i "%OPEN_FOLDER%"=="Y" (
        explorer "%PACKAGE_DIR%"
    )
) else (
    echo [ERROR] Failed to create ZIP package!
    pause
    exit /b 1
)

echo.
echo ===============================================
echo    Package creation completed successfully!
echo ===============================================
pause
