# utils/geocoder.py
# 功能：使用日本国土地理院（GSI）API 进行地理编码（免费，NLP/地图集成）
# 将地址转为经纬度（Lat, Lng）
# API 文档：https://msearch.gsi.go.jp/address-search/AddressSearch

import requests
import time
from utils.address_extractor import extract_address

def geocode_gsi(address: str):
    """
    地理编码：地址 → 经纬度。
    :param address: 日本地址字符串
    :return: (lat, lng) 元组；若失败，返回 (None, None)
    """
    url = "https://msearch.gsi.go.jp/address-search/AddressSearch"
    try:
        resp = requests.get(url, params={"q": address}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data and "features" in data and data["features"]:
            coord = data["features"][0]["geometry"]["coordinates"]
            return float(coord[1]), float(coord[0])  # lat, lng
        return None, None
    except requests.exceptions.Timeout:
        print(f"地理编码超时: {address}")
        return None, None
    except requests.exceptions.RequestException as e:
        print(f"地理编码网络错误: {e}")
        return None, None
    except Exception as e:
        print(f"地理编码错误: {e}")
        return None, None

def geocode_nominatim(address: str, country_code="jp"):
    """
    备用地理编码：使用 OpenStreetMap Nominatim API
    :param address: 地址字符串（支持日文或英文）
    :param country_code: 国家代码，默认 "jp"（日本）
    :return: (lat, lng) 元组；若失败，返回 (None, None)
    """
    url = "https://nominatim.openstreetmap.org/search"
    headers = {
        "User-Agent": "FCL-Checker/1.0"
    }
    
    # 构建查询参数
    params = {
        "q": address,
        "format": "json",
        "limit": 1,
        "addressdetails": 1
    }
    
    # 如果指定了国家代码，添加到参数中
    if country_code:
        params["countrycodes"] = country_code
    
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data and len(data) > 0:
            result = data[0]
            # 验证结果是否在日本（如果指定了日本）
            if country_code == "jp":
                country = result.get("address", {}).get("country_code", "").upper()
                if country and country != "JP":
                    print(f"警告：地址不在日本境内: {address}")
            return float(result["lat"]), float(result["lon"])
        return None, None
    except Exception as e:
        print(f"Nominatim 地理编码错误: {e}")
        return None, None


def geocode(address: str):
    """
    智能地理编码：先尝试 GSI，失败则使用 Nominatim，最后尝试提取地址部分
    支持日文和英文地址
    :param address: 地址字符串（日文或英文）
    :return: (lat, lng) 元组；若失败，返回 (None, None)
    """
    original_address = address
    
    # 检查是否为英文地址（简单判断：是否包含日文字符）
    is_japanese = any('\u3040' <= c <= '\u309F' or  # 平假名
                     '\u30A0' <= c <= '\u30FF' or  # 片假名
                     '\u4E00' <= c <= '\u9FFF'     # 汉字
                     for c in address)
    
    # 如果是日文地址，先尝试 GSI
    if is_japanese:
        lat, lng = geocode_gsi(address)
        if lat and lng:
            return lat, lng
        print(f"GSI 失败，尝试 Nominatim: {address}")
    else:
        print(f"检测到英文地址，使用 Nominatim: {address}")
    
    # 使用 Nominatim（支持英文和日文）
    time.sleep(1)  # Nominatim 要求请求间隔至少 1 秒
    
    # 先尝试限定日本
    lat, lng = geocode_nominatim(address, country_code="jp")
    if lat and lng:
        return lat, lng
    
    # 如果失败，尝试不限定国家（可能地址格式特殊）
    print(f"限定日本失败，尝试全球搜索: {address}")
    time.sleep(1)
    lat, lng = geocode_nominatim(address + ", Japan", country_code=None)
    if lat and lng:
        return lat, lng
    
    # 最后尝试：提取地址部分（去除建筑物名称）
    if is_japanese:
        extracted = extract_address(original_address)
        if extracted != original_address:
            print(f"尝试提取的地址部分: {extracted}")
            time.sleep(1)
            lat, lng = geocode_gsi(extracted)
            if lat and lng:
                return lat, lng
            time.sleep(1)
            lat, lng = geocode_nominatim(extracted, country_code="jp")
            if lat and lng:
                return lat, lng
    
    return None, None
