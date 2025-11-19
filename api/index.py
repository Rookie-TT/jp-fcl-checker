# api/index.py
print(">>> index.py 正在加载...")

import os
from flask import Flask, render_template, request, jsonify
import math
import yaml
import requests

# ================== 路径终极稳定方案 ==================
if os.getenv("VERCEL"):
    BASE_DIR = "/var/task"
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
CONFIG_DIR   = os.path.join(BASE_DIR, "config")

app = Flask(__name__, template_folder=TEMPLATE_DIR)

# 加载港口配置（只加载一次，全局共享）
PORTS_PATH = os.path.join(CONFIG_DIR, "ports.yaml")
with open(PORTS_PATH, encoding="utf-8") as f:
    PORTS = yaml.safe_load(f)["destination_ports"]

# 导入工具
from utils.geocoder import geocode_gsi
from utils.osm_roads import query_osm_roads
from utils.rules import can_access_fcl, PORTS as RULES_PORTS  # 防止 rules 里再读一次
from utils.jp_address_parser_simple import parse

# Haversine 距离计算
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

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/check", methods=["POST"])
def check():
    addresses = request.json.get("addresses", [])
    if isinstance(addresses, str):
        addresses = [addresses.strip()]
    if not addresses:
        return jsonify({"error": "住所を入力してください"})

    results = []
    for addr in addresses:
        addr = addr.strip()
        if not addr:
            continue

        # 1. 地址解析
        parsed = {"full": addr, "prefecture": "", "city": "", "town": "", "rest": ""}
        try:
            parsed.update(parse(addr)._asdict())
        except:
            pass

        # 2. 地理编码
        lat, lng = geocode_gsi(addr)
        if not lat:
            results.append({"address": addr, "error": "座標が取得できませんでした"})
            continue

        # 3. OSM 道路
        roads = query_osm_roads(lat, lng)

        # 4. 可达性判断
        can_access, reason = can_access_fcl(roads, parsed)

        # 5. 最近港口
        port_info = get_nearest_port(lat, lng)

        results.append({
            "address": addr,
            "can_access": can_access,
            "reason": reason,
            "nearest_port": f"{port_info['name']}（{port_info['code']}）",
            "distance": f"約{port_info['distance']}km",
            "estimated_time": f"予想牽引時間：{port_info['estimated_time']}"
        })

    return jsonify({"results": results})

# Vercel 必需
from mangum import Mangum
handler = Mangum(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
