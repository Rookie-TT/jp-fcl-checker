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
    判断是否可收整箱（改进版：考虑单向车道、转弯半径、设施类型）
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
    
    # ========== 白名单：工业/物流设施（优先级最高）==========
    # 这些地方通常有足够的空间和转弯半径
    industrial_keywords = [
        # 港口/码头
        "ふ頭", "埠頭", "港", "港湾",
        # 工业区
        "工業団地", "工業地帯", "工場", "製造所", "事業所",
        # 物流设施
        "物流センター", "物流基地", "配送センター", "倉庫", "デポ",
        # 其他
        "流通センター", "卸売市場"
    ]
    if any(keyword in full_address for keyword in industrial_keywords):
        return True, f"工業・物流施設、{vehicle_name}対応可能（広い敷地・転回スペース確保）"
    
    # ========== 黑名单：不可达区域（优先级第二）==========
    
    # 1. 高层建筑（楼层信息）
    # 只有明确的楼层信息才判断为高层建筑
    import re
    # 匹配：3階、5F、10階建て等
    floor_pattern = r'[0-9０-９]+[階F]|[0-9０-９]+階建'
    if re.search(floor_pattern, full_address):
        return False, "高層ビル・商業施設内、コンテナ車進入不可"
    
    # 明确的高层建筑关键词
    if "タワー" in full_address or "ビル" in full_address:
        # 但如果是工业设施的一部分，可能可达
        if not any(kw in full_address for kw in ["工場", "倉庫", "物流"]):
            return False, "高層ビル・商業施設内、コンテナ車進入不可"
    
    # 2. 商业区/繁华街（道路狭窄、转弯困难）
    # 只检查明确的商业区关键词，避免误判普通町名
    commercial_keywords = [
        "銀座", "祇園", "表参道", "原宿", "渋谷中心", "新宿駅", "池袋駅",
        "商店街", "アーケード", "駅前ビル", "駅ビル", "ショッピングモール"
    ]
    if any(keyword in full_address for keyword in commercial_keywords):
        return False, "商業地区・繁華街、道路狭小・転回困難でコンテナ車進入不可"
    
    # 3. 古街/观光地（道路狭窄、历史保护）
    historic_keywords = [
        "町家", "花見小路", "古街", "旧市街", "歴史地区",
        "博物館", "神社", "寺", "城"
    ]
    if any(keyword in full_address for keyword in historic_keywords):
        return False, "歴史地区・観光地、道路狭小・文化財保護のためコンテナ車進入不可"
    
    # 4. 住宅密集区（道路狭窄、转弯困难）
    residential_keywords = [
        "住宅街", "団地", "マンション", "アパート"
    ]
    has_residential = any(keyword in full_address for keyword in residential_keywords)
    
    # 5. 公共设施（通常不适合大型车辆）
    public_keywords = [
        "動物園", "公園", "遊園地", "スタジアム", "体育館"
    ]
    if any(keyword in full_address for keyword in public_keywords):
        return False, "公共施設、コンテナ車進入制限あり"
    
    # ========== 地址完整性检查 ==========
    if "株式会社" in full_address or "近く" in full_address or "付近" in full_address:
        return False, "住所不明確、詳細な住所確認が必要"
    
    # ========== 道路数据分析 ==========
    if not roads:
        # 如果没有道路数据，但地址看起来正常，给予保守判断
        if parsed.get("city") and parsed.get("town"):
            return False, "周辺道路データ取得失敗、現地確認推奨"
        return False, "住所解析不可、詳細確認必要"
    
    # 过滤无效道路类型（步行街、小路等）
    pedestrian_types = ["living_street", "pedestrian", "footway", "path", "steps", "cycleway"]
    valid_roads = [r for r in roads if r["type"] not in pedestrian_types]
    
    if not valid_roads:
        return False, "歩行者専用道路のみ、コンテナ車進入不可"
    
    # ========== 道路类型分析 ==========
    road_types = [r["type"] for r in valid_roads]
    
    # 高速公路/主干道（通常可达）
    major_roads = ["motorway", "trunk", "primary"]
    has_major_road = any(t in major_roads for t in road_types)
    
    # 次要道路
    secondary_roads = ["secondary", "tertiary"]
    has_secondary_road = any(t in secondary_roads for t in road_types)
    
    # 小路/服务道路
    minor_roads = ["residential", "service", "unclassified"]
    has_minor_road = any(t in minor_roads for t in road_types)
    
    # ========== 道路宽度分析（考虑单向车道）==========
    widths = [r["width"] for r in valid_roads if r["width"] is not None]
    
    if not widths:
        # 没有宽度数据，根据道路类型和设施类型综合判断
        if has_major_road:
            return True, f"主要幹線道路に接続、{vehicle_name}対応可能"
        elif has_secondary_road:
            if has_residential:
                return False, "住宅街の一般道路、転回スペース不足の可能性あり、現地確認必要"
            return True, f"一般道路、{vehicle_name}対応可能（要現地確認）"
        else:
            return False, "道路幅データなし、狭小道路の可能性あり、現地確認必要"
    
    max_width = max(widths)
    avg_width = sum(widths) / len(widths)
    
    # ========== 单向车道宽度计算 ==========
    # 假设双向道路，单向车道宽度约为总宽度的 40-45%
    # 考虑路边停车、路肩等因素
    effective_lane_width = max_width * 0.45
    
    # 车辆需要的实际宽度（考虑安全余量）
    # 车宽 + 左右各 0.3m 安全距离
    required_lane_width = vehicle_width + 0.6
    
    # ========== 转弯半径判断 ==========
    # 40ft 拖车转弯半径约 12-15m，需要较宽的道路
    # 如果是小路且没有工业设施，转弯可能困难
    turning_difficult = False
    if vehicle_type in ["40ft", "20ft"] and has_minor_road and not has_major_road:
        turning_difficult = True
    
    # ========== 综合判断 ==========
    
    # 情况1：道路很宽（总宽度 >= 最小要求 + 2m），单向车道足够
    if max_width >= min_width_required + 2.0:
        return True, f"道路幅{max_width:.1f}m（片側約{effective_lane_width:.1f}m）、{vehicle_name}対応可能"
    
    # 情况2：道路宽度刚好满足要求
    elif max_width >= min_width_required:
        if turning_difficult:
            return False, f"道路幅{max_width:.1f}m、転回スペース不足、{vehicle_name}進入困難"
        elif has_residential:
            return False, f"道路幅{max_width:.1f}m、住宅街で転回困難、{vehicle_name}進入不可"
        else:
            return True, f"道路幅{max_width:.1f}m、{vehicle_name}対応可能（転回スペース要確認）"
    
    # 情况3：道路宽度不足，但单向车道可能够用
    elif effective_lane_width >= required_lane_width:
        if has_major_road:
            return True, f"道路幅{max_width:.1f}m、片側車線で{vehicle_name}対応可能（要注意）"
        else:
            return False, f"道路幅{max_width:.1f}m、対向車とのすれ違い困難、{vehicle_name}進入不可"
    
    # 情况4：道路宽度明显不足
    else:
        return False, f"道路幅{max_width:.1f}m（片側約{effective_lane_width:.1f}m）、{vehicle_name}（最低{min_width_required}m必要）進入不可"


