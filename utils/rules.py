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

def can_access_fcl(roads, parsed, vehicle_type="40ft", original_address=None):
    """
    判断是否可收整箱（改进版：考虑单向车道、转弯半径、设施类型）
    :param roads: OSM 道路列表
    :param parsed: 解析后的地址
    :param vehicle_type: 车辆类型（40ft, 20ft, 10t, 4t, 2t）
    :param original_address: 原始地址（用于检查建筑物名称等信息）
    :return: (bool, str) - (可达, 日文理由)
    """
    # 获取车辆配置
    vehicle_config = VEHICLES.get(vehicle_type, VEHICLES["40ft"])
    min_width_required = vehicle_config["min_road_width"]
    vehicle_name = vehicle_config["name"]
    vehicle_width = vehicle_config["width"]
    
    # 使用原始地址（如果提供）或解析后的地址
    if original_address:
        full_address = original_address
    else:
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
        "流通センター", "卸売市場",
        # 特定工业区地名
        "向洋町", "六甲アイランド",  # 六甲岛工业区
        "深江浜", "深江浜町",  # 神户深江浜工业区
        # 英文关键词
        "FACTORY", "WAREHOUSE", "PLANT"
    ]
    
    # 检查日文和英文地址
    full_address_upper = full_address.upper()
    if any(keyword in full_address for keyword in industrial_keywords) or \
       any(keyword in full_address_upper for keyword in ["FACTORY", "WAREHOUSE", "PLANT"]):
        return True, f"工業・物流施設、{vehicle_name}対応可能（広い敷地・転回スペース確保）"
    
    # 特殊情况：如果地址包含"NO."或门牌号格式，且在农村/郊区（DISTRICT, TOWN等），可能是工厂
    # 但这个判断不够准确，建议用户在地址中明确标注"工場"或"FACTORY"
    
    # ========== 黑名单：不可达区域（优先级第二）==========
    
    # 1. 高层建筑（楼层信息）
    import re
    # 匹配：3階、5F、10階建て、35F等
    floor_pattern = r'[0-9０-９]+[階F]|[0-9０-９]+階建'
    if re.search(floor_pattern, full_address):
        return False, "高層ビル・商業施設内、コンテナ車進入不可"
    
    # 明确的高层建筑关键词
    high_rise_keywords = ["タワー", "ツインタワー", "スクエア"]
    if any(kw in full_address for kw in high_rise_keywords):
        # 但如果是工业设施的一部分，可能可达
        if not any(kw in full_address for kw in ["工場", "倉庫", "物流"]):
            return False, "高層ビル・商業施設内、コンテナ車進入不可"
    
    # "ビル"关键词需要更谨慎判断（很多地址都包含"ビル"）
    # 只有明确是商业大楼或写字楼才判断为不可达
    building_keywords = ["ビル", "センタービル", "オフィスビル"]
    if any(kw in full_address for kw in building_keywords):
        # 如果不是工业设施，且不是简单的地址描述，判断为商业大楼
        if not any(kw in full_address for kw in ["工場", "倉庫", "物流", "ふ頭", "港"]):
            # 检查是否有明确的大楼名称（通常包含公司名或建筑名）
            if any(kw in full_address for kw in ["生命", "センター", "オフィス"]) or \
               re.search(r'[A-Z]{2,}', full_address):  # 包含大写英文缩写
                return False, "高層ビル・商業施設内、コンテナ車進入不可"
    
    # 2. 商业区/繁华街（道路狭窄、转弯困难）
    # 检查明确的商业区关键词
    commercial_keywords = [
        "銀座", "祇園", "表参道", "原宿", "渋谷中心", "新宿駅", "池袋駅",
        "商店街", "アーケード", "駅前ビル", "駅ビル", "ショッピングモール",
        "109", "SHIBUYA109"  # 特定商业设施
    ]
    if any(keyword in full_address for keyword in commercial_keywords):
        return False, "商業地区・繁華街、道路狭小・転回困難でコンテナ車進入不可"
    
    # 车站附近商业区（但不包括工业区）
    # 注意：有些车站前道路很宽，可以通行，所以不能一刀切
    # 只对明确的商业设施进行限制
    station_commercial_keywords = ["駅ビル", "駅前ビル", "駅構内"]
    if any(kw in full_address for kw in station_commercial_keywords):
        return False, "駅前商業施設内、コンテナ車進入不可"
    
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
    
    # 检查是否为住宅区小路（生活道路）
    # 特征：地址中包含"丁目"但没有工业设施关键词
    is_residential_area = "丁目" in full_address and not any(kw in full_address for kw in ["工場", "倉庫", "物流", "ふ頭", "港"])
    
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
    pedestrian_types = ["pedestrian", "footway", "path", "steps", "cycleway"]
    valid_roads = [r for r in roads if r["type"] not in pedestrian_types]
    
    # 检查是否只有生活道路（living_street）- 这是住宅区的狭窄小路
    living_streets = [r for r in roads if r["type"] == "living_street"]
    if living_streets and not any(r["type"] not in ["living_street"] + pedestrian_types for r in roads):
        # 只有生活道路，大型车辆无法通行
        if vehicle_type in ["40ft", "20ft", "10t"]:
            return False, "生活道路（住宅街の狭小路）、大型車両進入不可"
    
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
    
    # ========== 道路宽度分析（优先考虑最近的道路）==========
    
    # ========== 只使用最近的道路进行判断（最后一段路）==========
    roads_with_distance = [r for r in valid_roads if r.get("distance") is not None]
    
    if roads_with_distance:
        # 按距离排序，只使用最近的道路（30米内）
        nearest_roads = sorted(roads_with_distance, key=lambda x: x["distance"])
        
        # 只考虑30米内的道路（最后一段路）
        last_mile_roads = [r for r in nearest_roads if r["distance"] <= 30]
        
        if not last_mile_roads:
            # 如果30米内没有道路，使用最近的3条道路
            last_mile_roads = nearest_roads[:3]
            min_distance = last_mile_roads[0]["distance"]
            print(f"  警告：最近道路距离{min_distance:.0f}m，判断可能不准确")
        
        # 使用最后一段路的宽度进行判断
        last_mile_widths = [r["width"] for r in last_mile_roads if r["width"] is not None]
        
        if not last_mile_widths:
            # 没有宽度数据，根据道路类型判断
            last_mile_types = [r["type"] for r in last_mile_roads]
            if any(t in ["living_street", "service", "footway", "path"] for t in last_mile_types):
                return False, "最終区間が狭小路・生活道路、道路幅データなし、現地確認必要"
            elif any(t in ["motorway", "trunk", "primary"] for t in last_mile_types):
                return True, f"最終区間が主要幹線道路、{vehicle_name}対応可能"
            else:
                return False, "最終区間の道路幅データなし、現地確認必要"
        
        # 使用最窄的道路宽度（因为车辆必须通过最窄的地方）
        max_width = max(last_mile_widths)
        min_width = min(last_mile_widths)
        avg_width = sum(last_mile_widths) / len(last_mile_widths)
        
        # 检查最后一段路的道路类型
        last_mile_types = [r["type"] for r in last_mile_roads]
        
        print(f"  最后一段路：{len(last_mile_roads)}条道路，宽度{min_width:.1f}-{max_width:.1f}m")
        
        # 优先级1：如果最后一段路包含主干道（primary/trunk），且宽度足够，判断为可达
        if any(t in ["motorway", "trunk", "primary"] for t in last_mile_types):
            # 主干道通常可达，但仍需检查最低宽度要求
            if max_width >= min_width_required:
                return True, f"最終区間が主要幹線道路（幅{max_width:.1f}m）、{vehicle_name}対応可能"
            else:
                return False, f"主要幹線道路だが道路幅{max_width:.1f}m不足、{vehicle_name}（最低{min_width_required}m必要）進入不可"
        
        # 优先级2：如果最后一段路是生活街道或服务道路，大型车辆无法通行
        if any(t in ["living_street", "service"] for t in last_mile_types):
            if vehicle_type in ["40ft", "20ft", "10t"]:
                return False, f"最終区間が生活道路・狭小路（幅{max_width:.1f}m）、{vehicle_name}進入不可"
            elif min_width < min_width_required:
                return False, f"最終区間道路幅{min_width:.1f}m、{vehicle_name}（最低{min_width_required}m必要）進入不可"
        
        # 如果最后一段路是住宅区道路（residential），需要更严格的判断
        if any(t == "residential" for t in last_mile_types):
            # 对于所有车辆，住宅区道路需要更宽的宽度（考虑路边停车、自行车、转弯等）
            if vehicle_type in ["40ft", "20ft"]:
                # 40ft/20ft拖车需要至少6米宽的住宅区道路
                if max_width < 6.0:
                    return False, f"最終区間が住宅街の狭小路（幅{max_width:.1f}m）、{vehicle_name}（転回困難・路上駐車あり）進入不可"
            elif vehicle_type == "10t":
                # 10t车需要至少5米宽的住宅区道路
                if max_width < 5.0:
                    return False, f"最終区間が住宅街の狭小路（幅{max_width:.1f}m）、{vehicle_name}（転回困難・路上駐車あり）進入不可"
            elif vehicle_type == "4t":
                # 4t车需要至少4.5米宽的住宅区道路
                if max_width < 4.5:
                    return False, f"最終区間が住宅街の狭小路（幅{max_width:.1f}m）、{vehicle_name}（転回困難・路上駐車あり）進入不可"
            elif vehicle_type == "2t":
                # 2t车需要至少4米宽的住宅区道路（考虑路边自行车、行人等）
                if max_width < 4.0:
                    return False, f"最終区間が住宅街の狭小路（幅{max_width:.1f}m）、{vehicle_name}（路上駐車・自転車あり）進入不可"
                # 即使4米宽，也要警告可能有困难
                elif max_width <= 4.0:
                    return False, f"最終区間が住宅街の狭小路（幅{max_width:.1f}m）、{vehicle_name}（路上駐車・自転車により実質通行困難）進入不可"
        
        # 使用最窄的道路宽度进行判断（车辆必须能通过最窄的地方）
        max_width = min_width
        avg_width = min_width
    else:
        # 没有距离信息，使用原有逻辑（向后兼容）
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
        print(f"  警告：使用周边所有道路进行判断（无距离信息）")
    
    # ========== 单向车道宽度计算 ==========
    # 假设双向道路，单向车道宽度约为总宽度的 40-45%
    # 考虑路边停车、路肩等因素
    effective_lane_width = max_width * 0.45
    
    # 车辆需要的实际宽度（考虑安全余量）
    # 车宽 + 左右各 0.3m 安全距离
    required_lane_width = vehicle_width + 0.6
    
    # 对向车辆通行所需宽度
    # 假设对向车辆为普通车（宽约2m）+ 安全余量0.5m
    oncoming_vehicle_width = 2.5
    
    # 双向通行所需最小宽度
    min_width_for_two_way = required_lane_width + oncoming_vehicle_width
    
    # ========== 转弯半径判断 ==========
    # 40ft 拖车转弯半径约 12-15m，需要较宽的道路
    # 如果是小路且没有工业设施，转弯可能困难
    turning_difficult = False
    if vehicle_type in ["40ft", "20ft"] and has_minor_road and not has_major_road:
        turning_difficult = True
    
    # ========== 综合判断 ==========
    
    # 情况1：道路足够宽，可以双向通行（不影响对向车辆）
    if max_width >= min_width_for_two_way:
        return True, f"道路幅{max_width:.1f}m、{vehicle_name}対応可能（対向車通行に支障なし）"
    
    # 情况2：道路宽度满足车辆要求，但可能影响对向车辆
    elif max_width >= min_width_required + 1.5:
        if turning_difficult:
            return False, f"道路幅{max_width:.1f}m、転回スペース不足、{vehicle_name}進入困難"
        elif has_residential or is_residential_area:
            # 住宅区道路，即使宽度够，也要考虑实际情况（路边停车、转弯等）
            return False, f"道路幅{max_width:.1f}m、住宅街で転回困難・路上駐車あり、{vehicle_name}進入不可"
        else:
            # 可以通行，但需要注意对向车辆
            return True, f"道路幅{max_width:.1f}m、{vehicle_name}対応可能（対向車通行時は一時停止必要）"
    
    # 情况3：道路宽度刚好满足车辆要求
    elif max_width >= min_width_required:
        if has_major_road:
            # 主干道可能有交通管制
            return True, f"道路幅{max_width:.1f}m、{vehicle_name}対応可能（対向車通行時は待避所利用必要）"
        else:
            # 小路无法安全通行
            return False, f"道路幅{max_width:.1f}m、対向車とのすれ違い不可、{vehicle_name}進入不可"
    
    # 情况4：单向车道勉强够用
    elif effective_lane_width >= required_lane_width:
        # 即使单向车道够用，也不能影响对向车辆
        return False, f"道路幅{max_width:.1f}m、対向車通行を妨げるため{vehicle_name}進入不可"
    
    # 情况5：道路宽度明显不足
    else:
        return False, f"道路幅{max_width:.1f}m（片側約{effective_lane_width:.1f}m）、{vehicle_name}（最低{min_width_required}m必要）進入不可"


