@echo off
:: Legacy batch file wrapper for new build system
:: Calls the modern PowerShell build script

echo ================================================
echo   Osmosis Build System (Legacy Wrapper)
echo ================================================
echo.

:: Check if PowerShell is available
powershell -Command "Write-Host 'PowerShell Available'" >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: PowerShell not available, falling back to Python build script
    if "%1"=="" (
        python build.py
    ) else (
        python build.py %*
    )
    goto :end
)

:: Use PowerShell build script
if "%1"=="" (
    powershell -ExecutionPolicy Bypass -File build.ps1 help
) else (
    powershell -ExecutionPolicy Bypass -File build.ps1 %*
)

:end
pause
