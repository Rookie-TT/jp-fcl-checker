# api/debug.py
# 专门用来逼 Vercel 吐出真实错误！

import os
import sys
import traceback

# 强制把所有错误输出到 stderr（Vercel 一定会显示）
def force_show_error():
    try:
        # 故意执行你原来的入口代码
        from api.index import app, handler
        print("如果能看到这行，说明你原来的代码其实没问题！")
    except Exception as e:
        print("="*60, file=sys.stderr)
        print("FCL-Checker 真实崩溃原因如下：", file=sys.stderr)
        print("="*60, file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print("="*60, file=sys.stderr)
        sys.exit(1)

force_show_error()