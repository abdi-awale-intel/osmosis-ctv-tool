@echo off
title Osmosis Installer
color 0B

echo.
echo   ██████╗ ███████╗███╗   ███╗ ██████╗ ███████╗██╗███████╗
echo  ██╔═══██╗██╔════╝████╗ ████║██╔═══██╗██╔════╝██║██╔════╝
echo  ██║   ██║███████╗██╔████╔██║██║   ██║███████╗██║███████╗
echo  ██║   ██║╚════██║██║╚██╔╝██║██║   ██║╚════██║██║╚════██║
echo  ╚██████╔╝███████║██║ ╚═╝ ██║╚██████╔╝███████║██║███████║
echo   ╚═════╝ ╚══════╝╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚═╝╚══════╝
echo.
echo  Osmosis Installer
echo  ========================
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
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

echo Copying application files...
copy "Osmosis.exe" "%INSTALL_DIR%\" >nul
if exist "config.json" copy "config.json" "%INSTALL_DIR%\" >nul
if exist "resources" xcopy "resources" "%INSTALL_DIR%\resources\" /E /I /Q >nul

echo Creating desktop shortcut...
powershell -command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\Osmosis.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\Osmosis.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = 'Osmosis Data Processor'; $Shortcut.Save()"

echo.
echo ================================
echo Installation completed successfully!
echo ================================
echo.
echo Osmosis has been installed to: %INSTALL_DIR%
echo Desktop shortcut created: Osmosis.lnk
echo.
echo You can now launch Osmosis from:
echo 1. Desktop shortcut
echo 2. Installation folder: %INSTALL_DIR%\Osmosis.exe
echo.

pause
