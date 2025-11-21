#!/bin/bash
# Vercel 部署脚本 (Linux/Mac)

echo "========================================"
echo "JP FCL Checker - Vercel 部署"
echo "========================================"
echo ""

# 检查是否安装了 Vercel CLI
if ! command -v vercel &> /dev/null; then
    echo "[错误] 未检测到 Vercel CLI"
    echo ""
    echo "请先安装 Vercel CLI:"
    echo "  npm install -g vercel"
    echo ""
    echo "或者通过 Vercel 网站部署:"
    echo "  https://vercel.com/new"
    echo ""
    exit 1
fi

echo "[1/3] 检查项目文件..."

if [ ! -f "api/index.py" ]; then
    echo "[错误] 找不到 api/index.py"
    exit 1
fi

if [ ! -f "vercel.json" ]; then
    echo "[错误] 找不到 vercel.json"
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    echo "[错误] 找不到 requirements.txt"
    exit 1
fi

echo "[✓] 项目文件检查完成"
echo ""

echo "[2/3] 准备部署..."
echo ""

# 询问部署类型
echo "选择部署类型:"
echo "  1. 预览部署 (Preview)"
echo "  2. 生产部署 (Production)"
echo ""
read -p "请输入选项 (1 或 2): " deploy_type

echo ""

if [ "$deploy_type" = "1" ]; then
    echo "[3/3] 开始预览部署..."
    vercel
elif [ "$deploy_type" = "2" ]; then
    echo "[3/3] 开始生产部署..."
    vercel --prod
else
    echo "[错误] 无效选项"
    exit 1
fi

echo ""
echo "========================================"
echo "部署完成！"
echo "========================================"
echo ""
