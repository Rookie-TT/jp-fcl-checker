# api/debug.py
# 终极强制报错版 —— Vercel 再也藏不住了！

import os
import sys
import traceback

print("=== FCL Checker 强制调试模式启动 ===", file=sys.stderr)

# 强制显示当前工作目录和文件列表（看看到底解压了啥）
print(f"当前工作目录: {os.getcwd()}", file=sys.stderr)
print("目录内容:", os.listdir("."), file=sys.stderr)
if os.path.exists("api"):
    print("api 文件夹内容:", os.listdir("api"), file=sys.stderr)
if os.path.exists("utils"):
    print("utils 文件夹内容:", os.listdir("utils"), file=sys.stderr)
if os.path.exists("config"):
    print("config 文件夹内容:", os.listdir("config"), file=sys.stderr)
if os.path.exists("templates"):
    print("templates 文件夹内容:", os.listdir("templates"), file=sys.stderr)

# 关键：强制导入你的主文件，让它在导入阶段就炸
try:
    print("正在强制导入 api/index.py ...", file=sys.stderr)
    from api.index import app
    # 如果能走到这里，说明代码没问题
    print("导入成功！你的代码其实没问题！", file=sys.stderr)
    # 必须提供 handler 给 Vercel
    from mangum import Mangum
    handler = Mangum(app)
    print("Mangum handler 创建成功！服务即将正常运行", file=sys.stderr)
except Exception as e:
    print("\n" + "="*80, file=sys.stderr)
    print("真实崩溃原因如下（终于抓到你了！）:", file=sys.stderr)
    print("="*80, file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    print("="*80, file=sys.stderr)
    print("请把上面红字错误复制给我，10秒解决！", file=sys.stderr)
    # 故意抛错，让 Vercel 显示 500
    raise
