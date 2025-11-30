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

def get_route_info(start_lat, start_lng, end_lat, end_lng, timeout=8):
    """
    使用 OSRM API 获取实际道路距离和时间
    :return: (distance_km, duration_minutes) 或 (None, None)
    """
    try:
        # OSRM API - 免费的路线规划服务
        url = f"http://router.project-osrm.org/route/v1/driving/{start_lng},{start_lat};{end_lng},{end_lat}"
        params = {
            "overview": "false",
            "steps": "false"
        }
        
        resp = requests.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        
        if data.get("code") == "Ok" and data.get("routes"):
            route = data["routes"][0]
            distance_m = route["distance"]  # 米
            duration_s = route["duration"]  # 秒
            
            distance_km = round(distance_m / 1000, 1)
            duration_min = int(duration_s / 60)
            
            return distance_km, duration_min
        
        return None, None
    except Exception as e:
        print(f"OSRM 路线查询失败: {e}")
        return None, None


def calculate_port_distance(lat, lng, port):
    """
    计算到指定港口的距离和时间
    :return: dict with name, code, distance, time
    """
    straight_dist = haversine(lat, lng, port["lat"], port["lng"])
    
    # 尝试获取实际道路距离和时间
    actual_distance, actual_duration = get_route_info(lat, lng, port["lat"], port["lng"])
    
    if actual_distance and actual_duration:
        distance = actual_distance
        truck_factor = 2.0
        total_minutes = int(actual_duration * truck_factor)
    else:
        # 使用估算方法
        road_distance_factor = 1.4
        distance = round(straight_dist * road_distance_factor, 1)
        avg_speed = 25
        total_minutes = int((distance / avg_speed) * 60)
    
    # 格式化时间字符串
    hours = total_minutes // 60
    mins = total_minutes % 60
    
    if hours > 0:
        time_str = f"{hours}時間{mins}分" if mins > 0 else f"{hours}時間"
    else:
        time_str = f"{mins}分"
    
    return {
        "name": port["name"],
        "code": port["code"],
        "distance": distance,
        "time": time_str,
        "minutes": total_minutes  # 用于排序
    }


def get_nearest_port(lat, lng):
    """获取最近的港口"""
    distances = [(p, haversine(lat, lng, p["lat"], p["lng"])) for p in PORTS]
    nearest = min(distances, key=lambda x: x[1])
    port = nearest[0]
    
    return calculate_port_distance(lat, lng, port)


def get_nearest_major_port(lat, lng):
    """
    获取最近的主要港口信息
    :return: dict with port info
    """
    # 筛选主要港口
    major_ports = [p for p in PORTS if p.get("type") == "main"]
    
    # 找到直线距离最近的主要港口
    distances = [(p, haversine(lat, lng, p["lat"], p["lng"])) for p in major_ports]
    nearest = min(distances, key=lambda x: x[1])
    port = nearest[0]
    
    return calculate_port_distance(lat, lng, port)
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
    try:
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
            
            # 0. 预检查：是否只有公司名（没有具体地址）
            company_only_keywords = ["株式会社", "有限会社", "合同会社", "Co.,Ltd", "Corporation", "Inc."]
            is_company_name = any(keyword in addr for keyword in company_only_keywords)
            
            # 检查是否有具体地址信息（都道府县、市区町村、番地等）
            has_location = any(suffix in addr for suffix in ["都", "道", "府", "県", "市", "区", "町", "村", "丁目", "番地", "-"])
            
            # 如果只有公司名，先尝试地理编码（可能在 POI 数据库中）
            # 如果找不到，再提示需要详细地址
            
            # 1. NLP 地址解析
            parsed = {"full": addr, "prefecture": "", "city": "", "town": "", "rest": ""}
            try:
                parsed.update(parse(addr)._asdict())
            except:
                pass
            
            # 2. 地图：地理编码
            lat, lng, used_address = geocode(addr)
            if not lat:
                # 地理编码失败
                if is_company_name and not has_location:
                    # 只有公司名，且找不到位置
                    # 检查是否包含设施类型关键词
                    facility_keywords = {
                        "倉庫": "倉庫施設",
                        "物流センター": "物流施設",
                        "配送センター": "配送施設",
                        "工場": "工場施設",
                        "事業所": "事業所",
                        "本社": "本社",
                        "支店": "支店",
                        "営業所": "営業所"
                    }
                    
                    facility_type = None
                    for keyword, ftype in facility_keywords.items():
                        if keyword in addr:
                            facility_type = ftype
                            break
                    
                    # 判断设施类型是否通常可达
                    accessible_facilities = ["倉庫施設", "物流施設", "配送施設", "工場施設"]
                    likely_accessible = facility_type in accessible_facilities
                    
                    if likely_accessible:
                        reason = f"会社名のみ（{facility_type}）で位置情報が見つかりません。以下をお試しください：\n1. 正確な会社名を確認して再入力\n2. 詳細住所（都道府県・市区町村・番地）を追加\n※ {facility_type}は通常コンテナ車対応可能な施設です。"
                    else:
                        reason = "会社名のみで位置情報が見つかりません。以下をお試しください：\n1. 正確な会社名を確認して再入力\n2. 詳細住所（都道府県・市区町村・番地）を追加"
                    
                    results.append({
                        "address": addr,
                        "can_access": False,
                        "reason": reason,
                        "error": "住所不明確"
                    })
                else:
                    # 普通地址找不到
                    results.append({
                        "address": addr,
                        "can_access": False,
                        "reason": "座標解析不可、住所を確認してください",
                        "error": "座標解析不可"
                    })
                continue
            
            # 3. 地图：OSM 道路
            roads = query_osm_roads(lat, lng)
            
            # 4. 规则：可达性判断（传入车辆类型和原始地址）
            can_access, reason = can_access_fcl(roads, parsed, vehicle_type, original_address=addr)
            
            # 5. 最近港口（所有港口中最近的）
            port_info = get_nearest_port(lat, lng)
            
            # 6. 最近的主要港口
            nearest_major_port = get_nearest_major_port(lat, lng)
            
            # 检查是否可能是区域中心点（缺少精确门牌号定位）
            location_note = None
            if used_address and addr != used_address:
                # 如果原地址有门牌号，但解析后的地址看起来像区域级别
                import re
                has_house_number_in_input = bool(re.search(r'\b\d+-\d+', addr))
                has_house_number_in_result = bool(re.search(r'\d+-\d+', used_address))
                
                if has_house_number_in_input and has_house_number_in_result:
                    # 检查是否只有区域名称（如：鳥取県大山町八重）
                    if not any(keyword in used_address for keyword in ["丁目", "番地", "号"]):
                        location_note = "※ 表示位置は地区の中心点です。正確な位置はGoogle Mapsで確認してください。"
            
            results.append({
                "address": addr,
                "used_address": used_address if used_address != addr else None,  # 实际使用的地址
                "can_access": can_access,
                "reason": reason,  # 日文理由
                "nearest_port": f"{port_info['name']}（{port_info['code']}）",
                "distance": f"約{port_info['distance']}km",
                "estimated_time": f"{port_info['time']}",
                "nearest_major_port": nearest_major_port,  # 最近的主要港口
                "lat": lat,  # 纬度
                "lng": lng,  # 经度
                "location_note": location_note  # 位置说明
            })
    
        return jsonify({"results": results})
    
    except Exception as e:
        # 捕获所有错误，返回 JSON 格式的错误信息
        import traceback
        error_detail = traceback.format_exc()
        print(f"Error in check(): {error_detail}")
        return jsonify({
            "error": "処理中にエラーが発生しました",
            "detail": str(e)
        }), 500

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







