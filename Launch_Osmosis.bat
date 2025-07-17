@echo off
title Osmosis
color 0A
echo.
echo   ██████╗ ███████╗███╗   ███╗ ██████╗ ███████╗██╗███████╗
echo  ██╔═══██╗██╔════╝████╗ ████║██╔═══██╗██╔════╝██║██╔════╝
echo  ██║   ██║███████╗██╔████╔██║██║   ██║███████╗██║███████╗
echo  ██║   ██║╚════██║██║╚██╔╝██║██║   ██║╚════██║██║╚════██║
echo  ╚██████╔╝███████║██║ ╚═╝ ██║╚██████╔╝███████║██║███████║
echo   ╚═════╝ ╚══════╝╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚═╝╚══════╝
echo.
echo  Starting OSMOSIS...
echo  Please wait while the application loads...
echo.

cd /d "C:\Users\abdiawal\Downloads\Scripts\_Current\deployment_package"
"C:\Users\abdiawal\My Programs\SQLPathFinder3\python3\python.exe" "C:\Users\abdiawal\Downloads\Scripts\_Current\deployment_package\ctvlist_gui.py"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Osmosis failed to start
    echo Please check the installation and try again
    echo.
)

pause
