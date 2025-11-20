@echo off
REM Vercel 部署脚本 (Windows)

echo ========================================
echo JP FCL Checker - Vercel 部署
echo ========================================
echo.

REM 检查是否安装了 Vercel CLI
where vercel >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 未检测到 Vercel CLI
    echo.
    echo 请先安装 Vercel CLI:
    echo   npm install -g vercel
    echo.
    echo 或者通过 Vercel 网站部署:
    echo   https://vercel.com/new
    echo.
    pause
    exit /b 1
)

echo [1/3] 检查项目文件...
if not exist "api\index.py" (
    echo [错误] 找不到 api\index.py
    pause
    exit /b 1
)

if not exist "vercel.json" (
    echo [错误] 找不到 vercel.json
    pause
    exit /b 1
)

if not exist "requirements.txt" (
    echo [错误] 找不到 requirements.txt
    pause
    exit /b 1
)

echo [✓] 项目文件检查完成
echo.

echo [2/3] 准备部署...
echo.

REM 询问部署类型
echo 选择部署类型:
echo   1. 预览部署 (Preview)
echo   2. 生产部署 (Production)
echo.
set /p deploy_type="请输入选项 (1 或 2): "

if "%deploy_type%"=="1" (
    echo.
    echo [3/3] 开始预览部署...
    vercel
) else if "%deploy_type%"=="2" (
    echo.
    echo [3/3] 开始生产部署...
    vercel --prod
) else (
    echo [错误] 无效选项
    pause
    exit /b 1
)

echo.
echo ========================================
echo 部署完成！
echo ========================================
echo.
pause
