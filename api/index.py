# api/index.py
# 2025 年 Vercel 终极可调试版 —— 每一行都带日志，永不迷路！

print("=== FCL Checker 开始加载 ===")

import os
import sys
from flask import Flask, render_template, request, jsonify
import math
import yaml
import requests

# ================== 路径判断 ==================
print(f"[1] 环境变量 VERCEL = {os.getenv('VERCEL')}")
if os.getenv("VERCEL"):
    BASE_DIR = "/var/task"
    print(f"[1] 检测到 Vercel 环境，使用 BASE_DIR = /var/task")
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"[1] 本地环境，BASE_DIR = {BASE_DIR}")

TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
CONFIG_DIR   = os.path.join(BASE_DIR, "config")
print(f"[1] templates 路径: {TEMPLATE_DIR}")
print(f"[1] config 路径: {CONFIG_DIR}")

# ================== Flask 初始化 ==================
app = Flask(__name__, template_folder=TEMPLATE_DIR)
print("[2] Flask 应用创建成功")

# ================== 加载 ports.yaml ==================
PORTS_PATH = os.path.join(CONFIG_DIR, "ports.yaml")
print(f"[3] 正在加载港口配置: {PORTS_PATH}")

try:
    with open(PORTS_PATH, encoding="utf-8") as f:
        PORTS = yaml.safe_load(f)["destination_ports"]
    print(f"[3] 港口配置加载成功！共 {len(PORTS)} 个港口")
except Exception as e:
    print(f"[3] 港口配置加载失败！错误: {e}")
    print("[3] 程序即将崩溃！这是最常见原因！")
    sys.exit(1)  # 强制退出，让 Vercel 显示错误

# ================== 导入工具模块 ==================
print("[4] 开始导入工具模块...")
try:
    from utils.geocoder import geocode_gsi
    print("[4] geocode_gsi 导入成功")
except Exception as e:
    print(f"[4] geocode_gsi 导入失败: {e}")
    raise

try:
    from utils.osm_roads import query_osm_roads
    print("[4] query_osm_roads 导入成功")
except Exception as e:
    print(f"[4] query_osm_roads 导入失败: {e}")
    raise

try:
    from utils.rules import can_access_fcl
    print("[4] can_access_fcl 导入成功 ← 最关键的一行！")
except Exception as e:
    print(f"[4] can_access_fcl 导入失败: {e}")
    raise

try:
    from utils.jp_address_parser_simple import parse
    print("[4] jp_address_parser_simple 导入成功")
except Exception as e:
    print(f"[4] parse 导入失败: {e}")
    raise

print("[4] 所有模块导入完成！")

# ================== 工具函数 ==================
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return round(R * c, 1)

def get_nearest_port(lat, lng):
    distances = [(p, haversine(lat, lng, p["lat"], p["lng"])) for p in PORTS]
    port, dist = min(distances, key=lambda x: x[1])
    hours = int(dist // 30)
    mins = int((dist % 30) / 30 * 60)
    time_str = f"{hours}時間{mins}分" if hours else f"{mins}分"
    return {
        "name": port["name"],
        "code": port["code"],
        "distance": dist,
        "estimated_time": time_str
    }

# ================== 路由 ==================
@app.route("/")
def index():
    print("[Route] 访问首页 /")
    try:
        return render_template("index.html")
    except Exception as e:
        print(f"[Route] 模板加载失败: {e}")
        return "index.html 未找到，请检查 templates 文件夹", 500

@app.route("/check", methods=["POST"])
def check():
    print("[Route] 收到 /check 请求")
    try:
        data = request.get_json()
        addresses = data.get("addresses", []) if data else []
        print(f"[Request] 收到地址数量: {len(addresses) if isinstance(addresses, list) else 1}")
    except:
        addresses = []

    if isinstance(addresses, str):
        addresses = [addresses.strip()]
    if not addresses:
        return jsonify({"error": "住所を入力してください"})

    results = []
    for i, addr in enumerate(addresses):
        addr = addr.strip()
        if not addr:
            continue
        print(f"[{i+1}] 正在处理地址: {addr}")

        # 1. 解析
        parsed = {"full": addr, "prefecture": "", "city": "", "town": "", "rest": ""}
        try:
            parsed.update(parse(addr)._asdict())
            print(f"[{i+1}] 地址解析成功: {parsed['prefecture']}{parsed['city']}{parsed['town']}")
        except Exception as e:
            print(f"[{i+1}] 地址解析失败: {e}")

        # 2. 地理编码
        print(f"[{i+1}] 正在地理编码...")
        lat, lng = geocode_gsi(addr)
        if not lat:
            results.append({"address": addr, "error": "座標が取得できませんでした"})
            print(f"[{i+1}] 地理编码失败")
            continue
        print(f"[{i+1}] 地理编码成功: {lat}, {lng}")

        # 3. OSM 道路
        print(f"[{i+1}] 查询周边道路...")
        roads = query_osm_roads(lat, lng)
        print(f"[{i+1}] 找到 {len(roads)} 条有宽度标注的道路")

        # 4. 判断
        can_access, reason = can_access_fcl(roads, parsed)
        print(f"[{i+1}] 判断结果: {'可能' if can_access else '不可'} - {reason}")

        # 5. 港口
        port_info = get_nearest_port(lat, lng)

        results.append({
            "address": addr,
            "can_access": can_access,
            "reason": reason,
            "nearest_port": f"{port_info['name']}（{port_info['code']}）",
            "distance": f"約{port_info['distance']}km",
            "estimated_time": f"予想牽引時間：{port_info['estimated_time']}"
        })

    print("[Route] /check 处理完成，返回结果")
    return jsonify({"results": results})

# ================== Vercel 必需 ==================
print("[Final] 正在包装 Mangum handler...")
from mangum import Mangum
handler = Mangum(app)
print("=== FCL Checker 加载完成！准备就绪 ===")

if __name__ == "__main__":
    print("本地开发模式启动")
    app.run(host="0.0.0.0", port=5000, debug=True)
