@echo off
title Osmosis Installer
color 0B

echo.
echo ================================================
echo.
echo    ####    ####  ####  ####    ####   ####  ####
echo   ##  ##  ##    ##  ## ##  ##  ##  ## ##    ##
echo   ##  ##  ##     ####  ##  ##  ##  ##  ###   ###
echo   ##  ##   ###   ##    ####    ##  ##    ##    ##
echo    ####     ###  ##    ##       ####  ####  ####
echo.
echo.
echo           OSMOSIS v2.0 INSTALLER
echo         Advanced CTV Tool Suite
echo       Intel Database Analysis Tool
echo.
echo ================================================
echo.

set "INSTALL_DIR=%USERPROFILE%\Desktop\Osmosis"

echo This will install Osmosis to: %INSTALL_DIR%
echo.
set /p confirm="Continue? (Y/N): "
if /i not "%confirm%"=="Y" (
    echo Installation cancelled.
    pause
    exit /b
)

echo.
echo Creating installation directory...
if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
    echo [✓] Directory created: %INSTALL_DIR%
) else (
    echo [!] Directory already exists: %INSTALL_DIR%
)

echo.
echo [1/4] Copying main executable...
if exist "Osmosis.exe" (
    copy "Osmosis.exe" "%INSTALL_DIR%\" >nul 2>&1
    if %errorlevel% equ 0 (
        echo [✓] Osmosis.exe copied successfully
    ) else (
        echo [✗] Failed to copy Osmosis.exe
        goto error
    )
) else (
    echo [✗] Osmosis.exe not found in current directory
    goto error
)

echo [2/4] Copying configuration files...
if exist "config.json" (
    copy "config.json" "%INSTALL_DIR%\" >nul 2>&1
    echo [✓] config.json copied
) else (
    echo [!] config.json not found (optional)
)

echo [3/4] Copying resource directories...
if exist "resources" (
    xcopy "resources" "%INSTALL_DIR%\resources\" /E /I /Q >nul 2>&1
    echo [✓] Resources directory copied
) else (
    echo [!] Resources directory not found (optional)
)
if exist "PyUber" (
    xcopy "PyUber" "%INSTALL_DIR%\PyUber\" /E /I /Q >nul 2>&1
    echo [✓] PyUber directory copied
)
if exist "Uber" (
    xcopy "Uber" "%INSTALL_DIR%\Uber\" /E /I /Q >nul 2>&1
    echo [✓] Uber directory copied
)

echo [4/4] Creating desktop shortcut...
echo [4/4] Creating desktop shortcut...
powershell -command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\Osmosis.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\Osmosis.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = 'Osmosis Data Processor'; $Shortcut.Save()" >nul 2>&1
if %errorlevel% equ 0 (
    echo [✓] Desktop shortcut created
) else (
    echo [!] Could not create desktop shortcut
)

echo.
echo ================================================
echo           INSTALLATION COMPLETED!
echo ================================================
echo.
echo [✓] Osmosis has been installed to:
echo     %INSTALL_DIR%
echo.
echo [✓] You can now launch Osmosis from:
echo     • Desktop shortcut: Osmosis.lnk
echo     • Start menu search: "Osmosis"  
echo     • Direct path: %INSTALL_DIR%\Osmosis.exe
echo.
echo ================================================
echo.
set /p launch="Launch Osmosis now? (Y/N): "
if /i "%launch%"=="Y" (
    echo.
    echo Launching Osmosis...
    start "" "%INSTALL_DIR%\Osmosis.exe"
)
echo.
echo Installation complete! Press any key to exit...
pause >nul
exit /b 0

:error
echo.
echo ================================================
echo           INSTALLATION FAILED!
echo ================================================
echo.
echo Please ensure:
echo 1. You're running as Administrator
echo 2. Osmosis.exe exists in the current directory
echo 3. You have write permissions to %USERPROFILE%\Desktop
echo.
echo Press any key to exit...
pause >nul
exit /b 1
echo.

pause
