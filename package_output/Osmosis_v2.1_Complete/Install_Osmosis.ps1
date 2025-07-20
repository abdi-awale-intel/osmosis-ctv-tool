# Osmosis PowerShell Installer
# Fast, modern installer with progress indicators

param(
    [string]$InstallPath = "$env:USERPROFILE\Desktop\Osmosis",
    [switch]$Silent = $false,
    [switch]$NoShortcut = $false
)

# Colors for output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($Args) {
        Write-Output $Args
    } else {
        $input | Write-Output
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Success { Write-ColorOutput Green $args }
function Write-Error { Write-ColorOutput Red $args }
function Write-Info { Write-ColorOutput Cyan $args }
function Write-Warning { Write-ColorOutput Yellow $args }

function Show-Banner {
    Clear-Host
    Write-Info ""
    Write-Info "================================================"
    Write-Info ""
    Write-Info "  ####   ####  #   #  ####   ####  ####  ####"
    Write-Info " #    # #      ## ##  #    # #      #    #"
    Write-Info " #    #  ###   # # #  #    #  ###   ###   ###"
    Write-Info " #    #     #  #   #  #    #     #     #     #"
    Write-Info "  ####  ####   #   #   ####  ####  ####  ####"
    Write-Info ""
    Write-Info "         OSMOSIS v2.0 INSTALLER"
    Write-Info "       Advanced CTV Tool Suite"
    Write-Info "     Intel Database Analysis Tool"
    Write-Info ""
    Write-Info "================================================"
    Write-Info ""
}

function Test-Prerequisites {
    Write-Info "[0/5] Checking prerequisites..."
    
    # Check if Osmosis.exe exists
    if (-not (Test-Path "Osmosis.exe")) {
        Write-Error "[✗] Osmosis.exe not found in current directory"
        return $false
    }
    
    # Check write permissions
    try {
        $testPath = Split-Path $InstallPath -Parent
        $testFile = Join-Path $testPath "test_write.tmp"
        New-Item -Path $testFile -ItemType File -Force | Out-Null
        Remove-Item $testFile -Force
    }
    catch {
        Write-Error "[✗] No write permissions to installation directory"
        return $false
    }
    
    Write-Success "[✓] Prerequisites check passed"
    return $true
}

function Install-Application {
    Write-Info "[1/5] Creating installation directory..."
    
    if (-not (Test-Path $InstallPath)) {
        New-Item -Path $InstallPath -ItemType Directory -Force | Out-Null
        Write-Success "[✓] Directory created: $InstallPath"
    } else {
        Write-Warning "[!] Directory already exists: $InstallPath"
    }
    
    Write-Info "[2/5] Copying main executable..."
    try {
        Copy-Item "Osmosis.exe" $InstallPath -Force
        Write-Success "[✓] Osmosis.exe copied successfully"
    }
    catch {
        Write-Error "[✗] Failed to copy Osmosis.exe: $_"
        return $false
    }
    
    Write-Info "[3/5] Copying configuration files..."
    
    # Copy config.json if it exists
    if (Test-Path "config.json") {
        Copy-Item "config.json" $InstallPath -Force
        Write-Success "[✓] config.json copied"
    } else {
        Write-Warning "[!] config.json not found (optional)"
    }
    
    # Copy README if it exists
    if (Test-Path "README.md") {
        Copy-Item "README.md" $InstallPath -Force
        Write-Success "[✓] README.md copied"
    }
    
    Write-Info "[4/5] Copying support directories..."
    
    # Copy directories if they exist
    $directories = @("resources", "PyUber", "Uber")
    foreach ($dir in $directories) {
        if (Test-Path $dir) {
            $destPath = Join-Path $InstallPath $dir
            Copy-Item $dir $destPath -Recurse -Force
            Write-Success "[✓] $dir directory copied"
        } else {
            Write-Warning "[!] $dir directory not found (optional)"
        }
    }
    
    return $true
}

function New-DesktopShortcut {
    if ($NoShortcut) {
        Write-Info "[5/5] Skipping desktop shortcut creation..."
        return $true
    }
    
    Write-Info "[5/5] Creating desktop shortcut..."
    
    try {
        $WshShell = New-Object -comObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\Osmosis.lnk")
        $Shortcut.TargetPath = Join-Path $InstallPath "Osmosis.exe"
        $Shortcut.WorkingDirectory = $InstallPath
        $Shortcut.Description = "Osmosis Data Processor v2.0"
        $Shortcut.Save()
        Write-Success "[✓] Desktop shortcut created"
        return $true
    }
    catch {
        Write-Warning "[!] Could not create desktop shortcut: $_"
        return $false
    }
}

function Show-CompletionMessage {
    Write-Success ""
    Write-Success "================================================"
    Write-Success "           INSTALLATION COMPLETED!"
    Write-Success "================================================"
    Write-Success ""
    Write-Success "[✓] Osmosis has been installed to:"
    Write-Success "    $InstallPath"
    Write-Success ""
    Write-Success "[✓] You can now launch Osmosis from:"
    Write-Success "    • Desktop shortcut: Osmosis.lnk"
    Write-Success "    • Start menu search: 'Osmosis'"
    Write-Success "    • Direct path: $InstallPath\Osmosis.exe"
    Write-Success ""
    Write-Success "================================================"
    Write-Success ""
    
    if (-not $Silent) {
        $launch = Read-Host "Launch Osmosis now? (Y/N)"
        if ($launch -eq "Y" -or $launch -eq "y") {
            Write-Info ""
            Write-Info "Launching Osmosis..."
            Start-Process (Join-Path $InstallPath "Osmosis.exe") -WorkingDirectory $InstallPath
        }
    }
}

function Show-ErrorMessage {
    Write-Error ""
    Write-Error "================================================"
    Write-Error "           INSTALLATION FAILED!"
    Write-Error "================================================"
    Write-Error ""
    Write-Error "Please ensure:"
    Write-Error "1. You're running as Administrator"
    Write-Error "2. Osmosis.exe exists in the current directory"
    Write-Error "3. You have write permissions to the installation path"
    Write-Error ""
    Write-Error "Installation path: $InstallPath"
    Write-Error ""
    
    if (-not $Silent) {
        Read-Host "Press Enter to exit"
    }
}

# Main installation process
function Start-Installation {
    Show-Banner
    
    if (-not $Silent) {
        Write-Info "This will install Osmosis to: $InstallPath"
        Write-Info ""
        $confirm = Read-Host "Continue? (Y/N)"
        if ($confirm -ne "Y" -and $confirm -ne "y") {
            Write-Info "Installation cancelled."
            return
        }
        Write-Info ""
    }
    
    # Start timer
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    
    try {
        if (-not (Test-Prerequisites)) { throw "Prerequisites check failed" }
        if (-not (Install-Application)) { throw "Application installation failed" }
        New-DesktopShortcut | Out-Null
        
        $stopwatch.Stop()
        Show-CompletionMessage
        Write-Info "Installation completed in $($stopwatch.Elapsed.TotalSeconds.ToString('F1')) seconds"
    }
    catch {
        $stopwatch.Stop()
        Write-Error "Installation failed: $_"
        Show-ErrorMessage
        exit 1
    }
}

# Run the installer
Start-Installation
