# utils/osm_roads.py
# 功能：使用 OpenStreetMap (OSM) Overpass API 查询周边道路（地图集成）
# 查询半径内道路宽度、类型（支持集装箱车可达性判断）

import requests

def query_osm_roads(lat, lng, radius=500):
    """
    查询 OSM 道路数据（改进版：即使没有宽度标注也返回道路类型）
    :param lat, lng: 地址经纬度
    :param radius: 查询半径（米，默认 500m）
    :return: 道路列表 [{"name": "", "width": float/None, "type": ""}]
    """
    overpass_url = "https://overpass-api.de/api/interpreter"
    
    # 查询所有道路（不仅限于有宽度标注的）
    query = f"""
    [out:json][timeout:15];
    way(around:{radius},{lat},{lng})["highway"];
    out tags;
    """
    
    try:
        resp = requests.post(overpass_url, data=query, timeout=15)
        resp.raise_for_status()
        elements = resp.json().get("elements", [])
        
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
            
            roads.append({
                "name": tags.get("name", tags.get("name:ja", "未知道路")),
                "width": width_val,
                "type": highway_type,
                "lanes": tags.get("lanes")
            })
        
        return roads
    except requests.exceptions.Timeout:
        print(f"OSM 查询超时: ({lat}, {lng})")
        return []
    except requests.exceptions.RequestException as e:
        print(f"OSM 网络错误: {e}")
        return []
    except Exception as e:
        print(f"OSM 查询错误: {e}")
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
