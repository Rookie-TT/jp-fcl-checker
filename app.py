# app.py
# 功能：Flask 主程序 - 处理地址输入 → NLP 解析 → 地图查询 → 规则判断 → 日文输出
# 集成：地址 NLP + GSI Geocoding + OSM 道路 + Haversine 距离 + LLM-like 理由生成（规则基）
# 运行：python app.py → http://localhost:5000

from flask import Flask, render_template, request, jsonify
import math
import yaml
import requests
from jp_address_parser import parse  # NLP 集成

app = Flask(__name__)

# 加载港口配置
with open("config/ports.yaml", encoding="utf-8") as f:
    PORTS = yaml.safe_load(f)["destination_ports"]

def haversine(lat1, lon1, lat2, lon2):
    """Haversine 公式：计算两点间距离（km，地图集成）。"""
    R = 6371  # 地球半径
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return round(R * c, 1)

def geocode_gsi(address):
    """地理编码（utils/geocoder.py）。"""
    from utils.geocoder import geocode_gsi
    return geocode_gsi(address)

def query_osm_roads(lat, lng):
    """OSM 道路查询（utils/osm_roads.py）。"""
    from utils.osm_roads import query_osm_roads
    return query_osm_roads(lat, lng)

def can_access_fcl(roads, parsed):
    """可达性判断（utils/rules.py）。"""
    from utils.rules import can_access_fcl
    return can_access_fcl(roads, parsed)

def get_nearest_port(lat, lng):
    """最近港口推荐（距离 + 拖车时间估算）。"""
    distances = [(p, haversine(lat, lng, p["lat"], p["lng"])) for p in PORTS]
    nearest = min(distances, key=lambda x: x[1])
    port, dist = nearest
    # 估算拖车时间（平均 30km/h）
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
    """首页：渲染日文模板。"""
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

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
