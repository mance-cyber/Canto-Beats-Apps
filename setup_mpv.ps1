# PowerShell script to download and setup mpv for Canto-beats
# 下載並設置 mpv 播放器

Write-Host "🎬 正在設置 MPV 播放器..." -ForegroundColor Cyan
Write-Host ""

# Create temp directory
$tempDir = Join-Path $env:TEMP "mpv_setup"
if (-not (Test-Path $tempDir)) {
    New-Item -ItemType Directory -Path $tempDir | Out-Null
}

# Download mpv (latest build from shinchiro)
$mpvUrl = "https://github.com/shinchiro/mpv-winbuild-cmake/releases/latest/download/mpv-x86_64-v3.7z"
$mpvArchive = Join-Path $tempDir "mpv.7z"

Write-Host "📥 下載 MPV (這可能需要幾分鐘)..." -ForegroundColor Yellow
try {
    Invoke-WebRequest -Uri $mpvUrl -OutFile $mpvArchive -UseBasicParsing
    Write-Host "✅ 下載完成" -ForegroundColor Green
} catch {
    Write-Host "❌ 下載失敗: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "請手動下載:" -ForegroundColor Yellow
    Write-Host "  1. 訪問: https://sourceforge.net/projects/mpv-player-windows/files/libmpv/" -ForegroundColor White
    Write-Host "  2. 下載最新的 mpv-dev-x86_64-*.7z" -ForegroundColor White
    Write-Host "  3. 解壓到當前目錄,確保 libmpv-2.dll 和所有依賴 DLL 都在一起" -ForegroundColor White
    exit 1
}

# Check if 7z is available
$7zPath = (Get-Command "7z.exe" -ErrorAction SilentlyContinue).Source
if (-not $7zPath) {
    Write-Host "⚠️  需要 7-Zip 來解壓檔案" -ForegroundColor Yellow
    Write-Host "請:" -ForegroundColor White
    Write-Host "  1. 安裝 7-Zip: https://www.7-zip.org/" -ForegroundColor White
    Write-Host "  2. 或手動解壓 $mpvArchive 到當前目錄" -ForegroundColor White
    exit 1
}

# Extract
Write-Host "📦 正在解壓..." -ForegroundColor Yellow
$extractPath = Join-Path $tempDir "mpv_extracted"
& $7zPath x $mpvArchive -o"$extractPath" -y | Out-Null

# Copy all DLLs to project root
$projectRoot = $PSScriptRoot
Write-Host "📋 正在複製 DLL 文件..." -ForegroundColor Yellow

# Find and copy libmpv-2.dll and dependencies
Get-ChildItem -Path $extractPath -Filter "*.dll" -Recurse | ForEach-Object {
    Copy-Item $_.FullName -Destination $projectRoot -Force
    Write-Host "  ✓ $($_.Name)" -ForegroundColor Gray
}

# Cleanup
Write-Host "🧹 清理臨時文件..." -ForegroundColor Yellow
Remove-Item -Path $tempDir -Recurse -Force

Write-Host ""
Write-Host "✅ MPV 設置完成!" -ForegroundColor Green
Write-Host "請重新啟動應用程式以使用視頻播放功能" -ForegroundColor Cyan
