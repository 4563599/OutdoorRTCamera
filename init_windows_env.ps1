# ATLI 相机监控系统 - Windows 测试环境初始化脚本 (PowerShell)

Write-Host "================================================" -ForegroundColor Blue
Write-Host "   ATLI 相机监控系统 - Windows 测试环境初始化" -ForegroundColor Blue
Write-Host "================================================" -ForegroundColor Blue

$BaseDir = "D:\pic_back"
$UploadDir = "$BaseDir\atli_uploads"
$ProcessedDir = "$BaseDir\atli_processed"

Write-Host ""
Write-Host "创建测试目录结构..." -ForegroundColor Yellow

# 创建基础目录
if (-not (Test-Path $BaseDir)) {
    New-Item -ItemType Directory -Path $BaseDir -Force | Out-Null
    Write-Host "✅ 创建目录: $BaseDir" -ForegroundColor Green
} else {
    Write-Host "ℹ️  目录已存在: $BaseDir" -ForegroundColor Cyan
}

# 创建上传目录
if (-not (Test-Path $UploadDir)) {
    New-Item -ItemType Directory -Path $UploadDir -Force | Out-Null
    Write-Host "✅ 创建目录: $UploadDir" -ForegroundColor Green
} else {
    Write-Host "ℹ️  目录已存在: $UploadDir" -ForegroundColor Cyan
}

# 创建相机目录
$Camera1Dir = "$UploadDir\camera1"
if (-not (Test-Path $Camera1Dir)) {
    New-Item -ItemType Directory -Path $Camera1Dir -Force | Out-Null
    Write-Host "✅ 创建目录: $Camera1Dir" -ForegroundColor Green
} else {
    Write-Host "ℹ️  目录已存在: $Camera1Dir" -ForegroundColor Cyan
}

$Camera2Dir = "$UploadDir\camera2"
if (-not (Test-Path $Camera2Dir)) {
    New-Item -ItemType Directory -Path $Camera2Dir -Force | Out-Null
    Write-Host "✅ 创建目录: $Camera2Dir" -ForegroundColor Green
} else {
    Write-Host "ℹ️  目录已存在: $Camera2Dir" -ForegroundColor Cyan
}

# 创建处理目录
if (-not (Test-Path $ProcessedDir)) {
    New-Item -ItemType Directory -Path $ProcessedDir -Force | Out-Null
    Write-Host "✅ 创建目录: $ProcessedDir" -ForegroundColor Green
} else {
    Write-Host "ℹ️  目录已存在: $ProcessedDir" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Blue
Write-Host "          Windows 测试环境初始化完成" -ForegroundColor Blue
Write-Host "================================================" -ForegroundColor Blue
Write-Host ""

Write-Host "📁 监控目录:" -ForegroundColor White
Write-Host "   - $Camera1Dir" -ForegroundColor Gray
Write-Host "   - $Camera2Dir" -ForegroundColor Gray
Write-Host ""

Write-Host "📤 输出目录:" -ForegroundColor White
Write-Host "   - $ProcessedDir" -ForegroundColor Gray
Write-Host ""

Write-Host "🚀 现在可以运行系统了:" -ForegroundColor Green
Write-Host "   python RT_Pixel_Ex.py" -ForegroundColor Yellow
Write-Host ""

Write-Host "⚠️  注意: 请确保已安装所有依赖包" -ForegroundColor Red
Write-Host "   pip install -r requirements.txt" -ForegroundColor Yellow
Write-Host ""

# 检查Python和依赖
Write-Host "🔍 检查运行环境..." -ForegroundColor Yellow

# 检查Python
try {
    $PythonVersion = python --version 2>&1
    Write-Host "OK Python: $PythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR Python not installed or not in PATH" -ForegroundColor Red
}

# 检查配置文件
if (Test-Path "config.yaml") {
    Write-Host "OK Config file exists: config.yaml" -ForegroundColor Green

    # 尝试测试配置
    try {
        $ConfigTest = python config_loader.py 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "OK Config file format is correct" -ForegroundColor Green
        } else {
            Write-Host "WARNING Config file may have issues, please check dependencies" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "WARNING Cannot test config file, please ensure dependencies are installed" -ForegroundColor Yellow
    }
} else {
    Write-Host "ERROR Config file not found: config.yaml" -ForegroundColor Red
}

Write-Host ""
Write-Host "按任意键继续..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
