# utils/geocoder.py
# 功能：使用日本国土地理院（GSI）API 进行地理编码（免费，NLP/地图集成）
# 将地址转为经纬度（Lat, Lng）
# API 文档：https://msearch.gsi.go.jp/address-search/AddressSearch

import requests

def geocode_gsi(address: str):
    """
    地理编码：地址 → 经纬度。
    :param address: 日本地址字符串
    :return: (lat, lng) 元组；若失败，返回 (None, None)
    """
    url = "https://msearch.gsi.go.jp/address-search/AddressSearch"
    try:
        resp = requests.get(url, params={"q": address}, timeout=5)
        data = resp.json()
        if data and "features" in data and data["features"]:
            coord = data["features"][0]["geometry"]["coordinates"]
            return float(coord[1]), float(coord[0])  # lat, lng
        return None, None
    except Exception as e:
        print(f"地理编码错误: {e}")
        return None, None