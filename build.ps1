# Osmosis Build System - PowerShell Version
# Modern replacement for old batch files

param(
    [Parameter(Position=0)]
    [ValidateSet("clean", "deps", "wheel", "exe", "package", "full", "test", "version")]
    [string]$Command = "help",
    
    [Parameter(Position=1)]
    [string]$Version = ""
)

# Set error action preference
$ErrorActionPreference = "Stop"

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

function Show-Help {
    Write-Info "🔧 Osmosis Build System (PowerShell)"
    Write-Output ""
    Write-Output "Usage: .\build.ps1 [command] [options]"
    Write-Output ""
    Write-Output "Commands:"
    Write-Output "  clean       - Clean build artifacts"
    Write-Output "  deps        - Install dependencies"
    Write-Output "  wheel       - Build wheel package"
    Write-Output "  exe         - Build standalone executable"
    Write-Output "  package     - Create complete distribution package"
    Write-Output "  full        - Full build (clean + deps + exe + package)"
    Write-Output "  test        - Run tests"
    Write-Output "  version X.Y - Update version number"
    Write-Output ""
    Write-Output "Examples:"
    Write-Output "  .\build.ps1 full                # Complete build"
    Write-Output "  .\build.ps1 version 2.1        # Update to version 2.1"
    Write-Output "  .\build.ps1 exe                 # Build executable only"
}

function Invoke-Clean {
    Write-Info "🧹 Cleaning build artifacts..."
    
    $dirsToClean = @("build", "dist", "package_output\temp")
    foreach ($dir in $dirsToClean) {
        if (Test-Path $dir) {
            Remove-Item -Recurse -Force $dir
            Write-Output "   Removed: $dir"
        }
    }
    
    # Clean pycache
    Get-ChildItem -Recurse -Name "__pycache__" | Remove-Item -Recurse -Force
    
    Write-Success "✅ Clean complete!"
}

function Install-Dependencies {
    Write-Info "📦 Installing dependencies..."
    
    try {
        python -m pip install -r requirements.txt
        python -m pip install pyinstaller setuptools wheel
        Write-Success "✅ Dependencies installed!"
    }
    catch {
        Write-Error "❌ Failed to install dependencies: $_"
        exit 1
    }
}

function Build-Wheel {
    Write-Info "🏗️ Building wheel package..."
    
    try {
        python setup.py bdist_wheel
        Write-Success "✅ Wheel package built!"
    }
    catch {
        Write-Error "❌ Failed to build wheel: $_"
        exit 1
    }
}

function Build-Executable {
    Write-Info "🔨 Building standalone executable..."
    
    try {
        python -m PyInstaller --clean --noconfirm osmosis.spec
        Write-Success "✅ Executable built!"
    }
    catch {
        Write-Error "❌ Failed to build executable: $_"
        exit 1
    }
}

function New-Package {
    Write-Info "📦 Creating distribution package..."
    
    # Load config for version
    $config = Get-Content "config.json" | ConvertFrom-Json
    $version = $config.application.version
    
    $packageName = "Osmosis_v${version}_Complete"
    $packagePath = "package_output\$packageName"
    
    if (Test-Path $packagePath) {
        Remove-Item -Recurse -Force $packagePath
    }
    New-Item -ItemType Directory -Path $packagePath -Force | Out-Null
    
    # Copy executable
    $exeSource = "dist\Osmosis\Osmosis.exe"
    if (Test-Path $exeSource) {
        Copy-Item $exeSource "$packagePath\Osmosis.exe"
    }
    
    # Copy supporting files
    $supportFiles = @(
        "config.json",
        "README.md"
    )
    
    foreach ($file in $supportFiles) {
        if (Test-Path $file) {
            Copy-Item $file $packagePath
        }
    }
    
    # Copy installer from core_package
    if (Test-Path "core_package\Install_Osmosis.bat") {
        Copy-Item "core_package\Install_Osmosis.bat" $packagePath
    }
    
    # Copy directories
    $dirCopies = @(
        @("PyUber", "PyUber"),
        @("resources", "resources"),
        @("Uber", "Uber")
    )
    
    foreach ($dirPair in $dirCopies) {
        $srcDir = $dirPair[0]
        $dstDir = $dirPair[1]
        if (Test-Path $srcDir) {
            Copy-Item -Recurse $srcDir "$packagePath\$dstDir"
        }
    }
    
    # Create ZIP archive
    $zipPath = "package_output\$packageName.zip"
    if (Test-Path $zipPath) {
        Remove-Item $zipPath
    }
    Compress-Archive -Path "$packagePath\*" -DestinationPath $zipPath
    
    Write-Success "✅ Package created: $zipPath"
    Write-Success "📁 Package folder: $packagePath"
}

function Update-Version {
    param([string]$NewVersion)
    
    Write-Info "🔢 Updating version to $NewVersion..."
    
    $config = Get-Content "config.json" | ConvertFrom-Json
    $config.application.version = $NewVersion
    $config.application.build_date = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
    
    $config | ConvertTo-Json -Depth 10 | Set-Content "config.json"
    
    Write-Success "✅ Version updated!"
}

function Invoke-Tests {
    if (Test-Path "tests") {
        Write-Info "🧪 Running tests..."
        try {
            python -m pytest tests
            Write-Success "✅ Tests passed!"
            return $true
        }
        catch {
            Write-Error "❌ Tests failed: $_"
            return $false
        }
    } else {
        Write-Info "ℹ️ No tests found, skipping..."
        return $true
    }
}

function Invoke-FullBuild {
    Write-Info "🚀 Starting full build process..."
    
    Invoke-Clean
    Install-Dependencies
    
    if (Invoke-Tests) {
        Build-Executable
        New-Package
        Write-Success "🎉 Full build completed successfully!"
    } else {
        Write-Error "❌ Build stopped due to test failures"
        exit 1
    }
}

# Main script logic
switch ($Command.ToLower()) {
    "clean" { Invoke-Clean }
    "deps" { Install-Dependencies }
    "wheel" { Build-Wheel }
    "exe" { Build-Executable }
    "package" { New-Package }
    "test" { Invoke-Tests }
    "version" { 
        if ($Version -eq "") {
            Write-Error "❌ Version number required. Usage: .\build.ps1 version X.Y"
            exit 1
        }
        Update-Version $Version 
    }
    "full" { Invoke-FullBuild }
    "help" { Show-Help }
    default { 
        Write-Error "❌ Unknown command: $Command"
        Show-Help
        exit 1
    }
}
