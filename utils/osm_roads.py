# utils/osm_roads.py
# 功能：使用 OpenStreetMap (OSM) Overpass API 查询周边道路（地图集成）
# 查询半径内道路宽度、类型（支持集装箱车可达性判断）

import requests

def query_osm_roads(lat, lng, radius=500):
    """
    查询 OSM 道路数据。
    :param lat, lng: 地址经纬度
    :param radius: 查询半径（米，默认 500m）
    :return: 道路列表 [{"name": "", "width": float, "type": ""}]
    """
    overpass_url = "http://overpass-api.de/api/interpreter"
    query = f"""
    [out:json];
    way(around:{radius},{lat},{lng})["highway"]["width"];
    out tags;
    """
    try:
        resp = requests.post(overpass_url, data=query, timeout=10)
        elements = resp.json().get("elements", [])
        roads = []
        for e in elements:
            tags = e.get("tags", {})
            width = tags.get("width")
            if width and "m" in width:
                try:
                    width_val = float(width.replace("m", "").strip())
                    roads.append({
                        "name": tags.get("name", "未知道路"),
                        "width": width_val,
                        "type": tags.get("highway", "unknown")
                    })
                except ValueError:
                    continue
        return roads
    except Exception as e:
        print(f"OSM 查询错误: {e}")
        return []