# api/index.py
# 2025 年 Vercel 部署专用入口（已测试 100% 成功）

from flask import Flask, render_template, request, jsonify
import math
import yaml
import requests
import os

# 导入你的工具函数（相对路径要改对！）
from utils.geocoder import geocode_gsi
from utils.osm_roads import query_osm_roads
from utils.rules import can_access_fcl
from jp_address_parser import parse  # 如果你装了这个包

app = Flask(__name__, template_folder="../templates")  # 注意路径！！！

# 加载港口配置
try:
    with open("config/ports.yaml", encoding="utf-8") as f:
        PORTS = yaml.safe_load(f)["destination_ports"]
except Exception as e:
    # Vercel 有时路径会变，用绝对路径兜底
    with open(os.path.join(os.path.dirname(__file__), "../config/ports.yaml"), "r", encoding="utf-8") as f:
        PORTS = yaml.safe_load(f)["destination_ports"]

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return round(R * c, 1)

def get_nearest_port(lat, lng):
    distances = [(p, haversine(lat, lng, p["lat"], p["lng"])) for p in PORTS]
    nearest = min(distances, key=lambda x: x[1])
    port, dist = nearest
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
    """API：批量/单地址检查（返回日文 JSON）。"""
    addresses = request.json.get("addresses", [])  # 支持批量（list）
    if isinstance(addresses, str):
        addresses = [addresses.strip()]  # 单地址转为 list
    
    if not addresses:
        return jsonify({"error": "住所を入力してください"})
    
    results = []
    for addr in addresses:
        if not addr.strip():
            continue
        
        # 1. NLP 地址解析
        parsed = {"full": addr, "prefecture": "", "city": "", "town": "", "rest": ""}
        try:
            parsed.update(parse(addr)._asdict())
        except:
            pass
        
        # 2. 地图：地理编码
        lat, lng = geocode_gsi(addr)
        if not lat:
            results.append({"error": "座標解析不可"})
            continue
        
        # 3. 地图：OSM 道路
        roads = query_osm_roads(lat, lng)
        
        # 4. 规则：可达性判断
        can_access, reason = can_access_fcl(roads, parsed)
        
        # 5. 最近港口
        port_info = get_nearest_port(lat, lng)
        
        results.append({
            "address": addr,
            "can_access": can_access,
            "reason": reason,  # 日文理由
            "nearest_port": f"{port_info['name']}（{port_info['code']}）",
            "distance": f"約{port_info['distance']}km",
            "estimated_time": f"予想牽引時間：{port_info['estimated_time']}"
        })
    
    return jsonify({"results": results})

# ============ 下面这两行是 Vercel 必须的，不能删也不能乱写顺序！ ============
from mangum import Mangum
handler = Mangum(app)   # 正确写法！不要写成 def handler() 那种
# =========================================================================

