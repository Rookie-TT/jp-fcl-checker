# api/minimal.py
# 最小化调试版 —— 一步步导入，直到炸！

import sys
import traceback

def log_step(step, msg):
    print(f"[DEBUG Step {step}] {msg}", file=sys.stderr)

log_step(0, "=== 最小化调试启动 ===")

# Step 1: 测试基础依赖（Flask, pyyaml, requests）
try:
    log_step(1, "测试基础依赖...")
    import flask  # 小写测试
    import yaml   # 小写测试
    import requests
    log_step(1, "基础依赖 OK")
except Exception as e:
    log_step(1, f"基础依赖失败: {e}")
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

# Step 2: 测试路径 + 加载 ports.yaml
try:
    log_step(2, "测试路径和 ports.yaml...")
    import os
    if os.getenv("VERCEL"):
        BASE_DIR = "/var/task"
    else:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    CONFIG_DIR = os.path.join(BASE_DIR, "config")
    PORTS_PATH = os.path.join(CONFIG_DIR, "ports.yaml")
    log_step(2, f"BASE_DIR: {BASE_DIR}, CONFIG_DIR: {CONFIG_DIR}")
    log_step(2, f"文件存在? {os.path.exists(PORTS_PATH)}")
    if os.path.exists(PORTS_PATH):
        with open(PORTS_PATH, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        log_step(2, f"ports.yaml 加载成功: {len(data.get('destination_ports', []))} 个港口")
    else:
        log_step(2, "ports.yaml 不存在！文件结构问题")
        sys.exit(1)
except Exception as e:
    log_step(2, f"路径/ports.yaml 失败: {e}")
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

# Step 3: 测试 utils 模块导入（逐个加）
try:
    log_step(3, "测试 utils.geocoder...")
    from utils.geocoder import geocode_gsi
    log_step(3, "geocoder OK")
except Exception as e:
    log_step(3, f"geocoder 失败: {e}")
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

try:
    log_step(4, "测试 utils.osm_roads...")
    from utils.osm_roads import query_osm_roads
    log_step(4, "osm_roads OK")
except Exception as e:
    log_step(4, f"osm_roads 失败: {e}")
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

try:
    log_step(5, "测试 utils.rules...")
    from utils.rules import can_access_fcl
    log_step(5, "rules OK ← 最可能炸在这里！")
except Exception as e:
    log_step(5, f"rules 失败: {e}")
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

try:
    log_step(6, "测试 utils.jp_address_parser_simple...")
    from utils.jp_address_parser_simple import parse
    log_step(6, "parser OK")
except Exception as e:
    log_step(6, f"parser 失败: {e}")
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

# Step 7: 测试 mangum
try:
    log_step(7, "测试 mangum...")
    from mangum import Mangum
    log_step(7, "mangum OK")
except Exception as e:
    log_step(7, f"mangum 失败: {e}")
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

# Step 8: 测试 Flask app
try:
    log_step(8, "测试 Flask...")
    from flask import Flask
    app = Flask(__name__)
    log_step(8, "Flask OK")
except Exception as e:
    log_step(8, f"Flask 失败: {e}")
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

# 如果走到这里，全 OK！
log_step(9, "=== 所有测试通过！问题可能在路由或运行时 ===")
handler = Mangum(app)  # 必须提供给 Vercel