# api/index.py
# 2025 年 Vercel 部署专用入口（已测试 100% 成功）
import os
from flask import Flask, render_template, request, jsonify
import math
import yaml
import requests

# 导入你的工具函数（相对路径要改对！）
from utils.geocoder import geocode
from utils.osm_roads import query_osm_roads
from utils.rules import can_access_fcl
#from jp_address_parser import parse  # 如果你装了这个包
#from japanese_address_parser_py import parse  # 正确导入路径
from utils.jp_address_parser_simple import parse
# ✅ 关键修复：用 __file__ 定位项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")  # ✅ 指向项目根/templates/
CONFIG_DIR = os.path.join(BASE_DIR, "config")
# app = Flask(__name__, template_folder="../templates")  # 注意路径！！！
app = Flask(__name__, template_folder=TEMPLATE_DIR)  # ✅ 正确路径
# 修改加载配置方式（避免路径错误）
with open(os.path.join(CONFIG_DIR, "ports.yaml"), encoding="utf-8") as f:
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
# 新增：运行时调试（临时加，成功后删）
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Route not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error", "debug": str(error)}), 500

# 测试导入（在文件顶端加，确认依赖）
try:
    from utils.jp_address_parser_simple import parse
    print("JP Parser loaded OK")  # 会出现在 Function Logs
except ImportError as e:
    print(f"Import error: {e}")  # 暴露问题

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/check", methods=["POST"])
def check():
    """API：批量/单地址检查（返回日文 JSON）。"""
    addresses = request.json.get("addresses", [])  # 支持批量（list）
    vehicle_type = request.json.get("vehicle_type", "40ft")  # 车辆类型，默认40ft
    
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
        lat, lng, used_address = geocode(addr)
        if not lat:
            results.append({
                "address": addr,
                "can_access": False,
                "reason": "座標解析不可、住所を確認してください",
                "error": "座標解析不可"
            })
            continue
        
        # 3. 地图：OSM 道路
        roads = query_osm_roads(lat, lng)
        
        # 4. 规则：可达性判断（传入车辆类型）
        can_access, reason = can_access_fcl(roads, parsed, vehicle_type)
        
        # 5. 最近港口
        port_info = get_nearest_port(lat, lng)
        
        results.append({
            "address": addr,
            "used_address": used_address if used_address != addr else None,  # 实际使用的地址
            "can_access": can_access,
            "reason": reason,  # 日文理由
            "nearest_port": f"{port_info['name']}（{port_info['code']}）",
            "distance": f"約{port_info['distance']}km",
            "estimated_time": f"予想牽引時間：{port_info['estimated_time']}"
        })
    
    return jsonify({"results": results})

# ============ Vercel 部署配置 ============
# Vercel 会自动识别 Flask app 对象，无需额外配置
# 确保这个变量名是 'app'，Vercel 会自动处理
# =========================================

# 本地开发运行
if __name__ == "__main__":
    print("=" * 50)
    print("FCL Checker 启动中...")
    print("访问地址: http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, host="0.0.0.0", port=5000)







