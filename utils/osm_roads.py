# utils/osm_roads.py
# 功能：使用 OpenStreetMap (OSM) Overpass API 查询周边道路（地图集成）
# 查询半径内道路宽度、类型（支持集装箱车可达性判断）

import requests

def query_osm_roads(lat, lng, radius=100, include_distance=True):
    """
    查询 OSM 道路数据（改进版：返回道路到目标点的距离）
    :param lat, lng: 地址经纬度
    :param radius: 查询半径（米，默认 100m - 只查询最后一段路）
    :param include_distance: 是否计算道路到目标点的距离
    :return: 道路列表 [{"name": "", "width": float/None, "type": "", "distance": float}]
    """
    overpass_url = "https://overpass-api.de/api/interpreter"
    
    # 查询所有道路（包含几何信息以计算距离）
    query = f"""
    [out:json][timeout:15];
    way(around:{radius},{lat},{lng})["highway"];
    out geom;
    """
    
    try:
        resp = requests.post(overpass_url, data=query, timeout=25)
        resp.raise_for_status()
        data = resp.json()
        elements = data.get("elements", [])
        
        if not elements:
            print(f"  OSM 未返回道路数据（可能是查询超时或该区域无数据）")
        
        roads = []
        for e in elements:
            tags = e.get("tags", {})
            highway_type = tags.get("highway", "unknown")
            
            # 跳过非机动车道路
            if highway_type in ["footway", "path", "steps", "cycleway", "pedestrian"]:
                continue
            
            width = tags.get("width")
            width_val = None
            
            # 尝试解析宽度
            if width:
                try:
                    # 处理各种宽度格式：3.5, 3.5m, 3.5 m
                    width_str = width.replace("m", "").replace("M", "").strip()
                    width_val = float(width_str)
                except (ValueError, AttributeError):
                    pass
            
            # 如果没有明确宽度，根据道路类型估算
            if width_val is None:
                width_val = estimate_width_by_type(highway_type)
            
            # 计算道路到目标点的最短距离
            distance = None
            if include_distance and "geometry" in e:
                distance = calculate_min_distance(lat, lng, e["geometry"])
            
            roads.append({
                "name": tags.get("name", tags.get("name:ja", "未知道路")),
                "width": width_val,
                "type": highway_type,
                "lanes": tags.get("lanes"),
                "distance": distance
            })
        
        return roads
    except requests.exceptions.Timeout:
        print(f"  OSM 查询超时: ({lat}, {lng}) - 请稍后重试")
        return []
    except requests.exceptions.RequestException as e:
        print(f"  OSM 网络错误: {e}")
        return []
    except KeyError as e:
        print(f"  OSM 数据解析错误: {e}")
        return []
    except Exception as e:
        print(f"  OSM 查询错误: {e}")
        import traceback
        traceback.print_exc()
        return []


def estimate_width_by_type(highway_type):
    """
    根据道路类型估算宽度（日本标准）
    """
    width_map = {
        "motorway": 12.0,      # 高速公路
        "trunk": 10.0,         # 国道
        "primary": 8.0,        # 主要道路
        "secondary": 6.0,      # 次要道路
        "tertiary": 5.0,       # 三级道路
        "residential": 4.0,    # 住宅区道路
        "service": 3.0,        # 服务道路
        "living_street": 2.5,  # 生活街道
        "unclassified": 4.0,   # 未分类道路
    }
    return width_map.get(highway_type, 4.0)  # 默认 4m


def calculate_min_distance(target_lat, target_lng, geometry):
    """
    计算目标点到道路的最短距离（米）
    :param target_lat, target_lng: 目标点坐标
    :param geometry: OSM 道路几何数据（节点列表）
    :return: 最短距离（米）
    """
    import math
    
    min_distance = float('inf')
    
    # 遍历道路的所有节点
    for node in geometry:
        node_lat = node.get("lat")
        node_lng = node.get("lon")
        
        if node_lat is None or node_lng is None:
            continue
        
        # 使用 Haversine 公式计算距离
        # 简化版：适用于短距离
        lat_diff = math.radians(node_lat - target_lat)
        lng_diff = math.radians(node_lng - target_lng)
        
        a = (math.sin(lat_diff / 2) ** 2 + 
             math.cos(math.radians(target_lat)) * 
             math.cos(math.radians(node_lat)) * 
             math.sin(lng_diff / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = 6371000 * c  # 地球半径 6371km
        
        if distance < min_distance:
            min_distance = distance
    
    return min_distance if min_distance != float('inf') else None
