@echo off
REM ATLI 相机监控系统 - Windows 测试环境初始化脚本
echo ================================================
echo    ATLI 相机监控系统 - Windows 测试环境初始化
echo ================================================

set BASE_DIR=D:\pic_back
set UPLOAD_DIR=%BASE_DIR%\atli_uploads
set PROCESSED_DIR=%BASE_DIR%\atli_processed

echo.
echo 创建测试目录结构...

REM 创建基础目录
if not exist "%BASE_DIR%" (
    mkdir "%BASE_DIR%"
    echo ✅ 创建目录: %BASE_DIR%
) else (
    echo ℹ️  目录已存在: %BASE_DIR%
)

REM 创建上传目录
if not exist "%UPLOAD_DIR%" (
    mkdir "%UPLOAD_DIR%"
    echo ✅ 创建目录: %UPLOAD_DIR%
) else (
    echo ℹ️  目录已存在: %UPLOAD_DIR%
)

if not exist "%UPLOAD_DIR%\camera1" (
    mkdir "%UPLOAD_DIR%\camera1"
    echo ✅ 创建目录: %UPLOAD_DIR%\camera1
) else (
    echo ℹ️  目录已存在: %UPLOAD_DIR%\camera1
)

if not exist "%UPLOAD_DIR%\camera2" (
    mkdir "%UPLOAD_DIR%\camera2"
    echo ✅ 创建目录: %UPLOAD_DIR%\camera2
) else (
    echo ℹ️  目录已存在: %UPLOAD_DIR%\camera2
)

REM 创建处理目录
if not exist "%PROCESSED_DIR%" (
    mkdir "%PROCESSED_DIR%"
    echo ✅ 创建目录: %PROCESSED_DIR%
) else (
    echo ℹ️  目录已存在: %PROCESSED_DIR%
)

echo.
echo ================================================
echo           Windows 测试环境初始化完成
echo ================================================
echo.
echo 📁 监控目录:
echo    - %UPLOAD_DIR%\camera1
echo    - %UPLOAD_DIR%\camera2
echo.
echo 📤 输出目录:
echo    - %PROCESSED_DIR%
echo.
echo 🚀 现在可以运行系统了:
echo    python RT_Pixel_Ex.py
echo.
echo ⚠️  注意: 请确保已安装所有依赖包
echo    pip install -r requirements.txt
echo.

pause
