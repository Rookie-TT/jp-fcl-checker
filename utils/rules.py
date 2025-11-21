# utils/rules.py
# 功能：FCL 可达性规则引擎（含黑白名单）
# 判断逻辑：道路宽度 >= 3.5m + 黑名单（古街/步行街） + 白名单（工业区）

import yaml
import os

# 修复：用 __file__ 定位到项目根目录下的 config
def load_ports():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, "..", "config", "ports.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["destination_ports"]

def load_vehicles():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, "..", "config", "vehicles.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["vehicles"]

# 全局变量
PORTS = load_ports()
VEHICLES = load_vehicles()

def is_restricted_area(parsed):
    """检查是否在限制区域（黑名单）。"""
    # 黑名单：古街/商业区，无法进入集装箱车
    restricted = ["東山区", "祇園", "銀座", "谷中", "国際通り"]
    text = (parsed["city"] + parsed["town"] + parsed["rest"])
    return any(area in text for area in restricted)

def can_access_fcl(roads, parsed, vehicle_type="40ft"):
    """
    判断是否可收整箱（改进版：基于车辆类型的智能判断）
    :param roads: OSM 道路列表
    :param parsed: 解析后的地址
    :param vehicle_type: 车辆类型（40ft, 20ft, 10t, 4t, 2t）
    :return: (bool, str) - (可达, 日文理由)
    """
    # 获取车辆配置
    vehicle_config = VEHICLES.get(vehicle_type, VEHICLES["40ft"])
    min_width_required = vehicle_config["min_road_width"]
    vehicle_name = vehicle_config["name"]
    vehicle_width = vehicle_config["width"]
    full_address = parsed.get("full", "") + parsed.get("city", "") + parsed.get("town", "") + parsed.get("rest", "")
    
    # 白名单：已知工业/港口区（优先级最高）
    port_keywords = ["ふ頭", "埠頭", "港", "工業団地", "物流センター", "倉庫"]
    if any(keyword in full_address for keyword in port_keywords):
        return True, "港湾・工業地区に位置、道路幅12m以上、40HQ対応可能"
    
    # 黑名单：商业区/古街/高层建筑（优先级第二）
    restricted_keywords = [
        "銀座", "祇園", "表参道", "原宿", "渋谷109", "商店街", 
        "タワー", "ビル", "階", "F", "博物館", "動物園", "公園",
        "駅前", "駅近く", "町家", "花見小路"
    ]
    if any(keyword in full_address for keyword in restricted_keywords):
        # 检查是否有楼层信息
        if any(floor in full_address for floor in ["階", "F", "タワー", "ビル"]):
            return False, "高層ビル・商業施設内、コンテナ車進入不可"
        return False, "商業地区・古街・観光地、道路狭小でコンテナ車進入不可"
    
    # 检查是否只有公司名或模糊地址
    if "株式会社" in full_address or "近く" in full_address or "付近" in full_address:
        return False, "住所不明確、詳細な住所確認が必要"
    
    # 道路数据检查
    if not roads:
        # 如果没有道路数据，但地址看起来正常，给予保守判断
        if parsed.get("city") and parsed.get("town"):
            return False, "周辺道路データ取得失敗、現地確認推奨"
        return False, "住所解析不可、詳細確認必要"
    
    # 过滤无效道路类型（步行街等）
    valid_roads = [r for r in roads if r["type"] not in ["living_street", "pedestrian", "footway", "path", "steps"]]
    
    if not valid_roads:
        return False, "歩行者専用道路のみ、コンテナ車進入不可"
    
    # 检查道路宽度
    widths = [r["width"] for r in valid_roads if r["width"] is not None]
    if not widths:
        # 没有宽度数据，根据道路类型判断
        road_types = [r["type"] for r in valid_roads]
        if any(t in ["motorway", "trunk", "primary"] for t in road_types):
            return True, "主要幹線道路に接続、40HQ対応可能"
        elif any(t in ["secondary", "tertiary"] for t in road_types):
            return True, "一般道路、40HQ対応可能（要現地確認）"
        else:
            return False, "道路幅データなし、現地確認必要"
    
    max_width = max(widths)
    min_width = min(widths)
    
    # 根据车辆类型判断道路宽度
    if max_width >= min_width_required:
        if max_width >= min_width_required + 1.0:
            return True, f"道路幅{max_width:.1f}m、{vehicle_name}（幅{vehicle_width}m）対応可能"
        else:
            return True, f"道路幅{max_width:.1f}m、{vehicle_name}対応可能（要注意）"
    else:
        return False, f"最大道路幅{max_width:.1f}m、{vehicle_name}（最低{min_width_required}m必要）進入不可"


