# utils/geocoder.py
# 功能：使用日本国土地理院（GSI）API 进行地理编码（免费，NLP/地图集成）
# 将地址转为经纬度（Lat, Lng）
# API 文档：https://msearch.gsi.go.jp/address-search/AddressSearch

import requests
import time
from utils.address_extractor import extract_address

def geocode_gsi(address: str, timeout=8):
    """
    地理编码：地址 → 经纬度（日本国土地理院 API）
    :param address: 日本地址字符串
    :param timeout: 超时时间（秒）
    :return: (lat, lng) 元组；若失败，返回 (None, None)
    """
    url = "https://msearch.gsi.go.jp/address-search/AddressSearch"
    try:
        resp = requests.get(url, params={"q": address}, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        
        # GSI 返回的是列表，不是字典
        if isinstance(data, list) and len(data) > 0:
            # 列表格式
            feature = data[0]
            if "geometry" in feature and "coordinates" in feature["geometry"]:
                coord = feature["geometry"]["coordinates"]
                return float(coord[1]), float(coord[0])  # lat, lng
        elif isinstance(data, dict) and "features" in data and data["features"]:
            # 字典格式（旧版 API）
            coord = data["features"][0]["geometry"]["coordinates"]
            return float(coord[1]), float(coord[0])  # lat, lng
        
        return None, None
    except requests.exceptions.Timeout:
        print(f"GSI 超时: {address}")
        return None, None
    except requests.exceptions.RequestException as e:
        print(f"GSI 网络错误: {e}")
        return None, None
    except Exception as e:
        print(f"GSI 错误: {e}")
        return None, None

def geocode_nominatim(address: str, country_code="jp", timeout=8):
    """
    备用地理编码：使用 OpenStreetMap Nominatim API
    :param address: 地址字符串（支持日文或英文）
    :param country_code: 国家代码，默认 "jp"（日本）
    :param timeout: 超时时间（秒）
    :return: (lat, lng) 元组；若失败，返回 (None, None)
    """
    url = "https://nominatim.openstreetmap.org/search"
    headers = {
        "User-Agent": "FCL-Checker/1.0 (https://github.com/your-repo)"
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
        resp = requests.get(url, params=params, headers=headers, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        if data and len(data) > 0:
            result = data[0]
            return float(result["lat"]), float(result["lon"])
        return None, None
    except requests.exceptions.Timeout:
        print(f"Nominatim 超时: {address}")
        return None, None
    except requests.exceptions.RequestException as e:
        print(f"Nominatim 网络错误: {e}")
        return None, None
    except Exception as e:
        print(f"Nominatim 错误: {e}")
        return None, None


def geocode(address: str):
    """
    智能地理编码：优先 GSI（日本地址最准确），失败则尝试 Nominatim
    支持日文和英文地址
    :param address: 地址字符串（日文或英文）
    :return: (lat, lng) 元组；若失败，返回 (None, None)
    """
    original_address = address
    
    # 检查是否为日文地址
    is_japanese = any('\u3040' <= c <= '\u309F' or  # 平假名
                     '\u30A0' <= c <= '\u30FF' or  # 片假名
                     '\u4E00' <= c <= '\u9FFF'     # 汉字
                     for c in address)
    
    # 策略1: 日文地址优先使用 GSI（日本国土地理院，最准确）
    if is_japanese:
        print(f"[1/4] GSI: {address}")
        lat, lng = geocode_gsi(address, timeout=8)
        if lat and lng:
            print(f"  ✓ GSI 成功")
            return lat, lng
    
    # 策略2: 尝试 Nominatim
    print(f"[2/4] Nominatim: {address}")
    time.sleep(0.3)
    lat, lng = geocode_nominatim(address, country_code="jp", timeout=8)
    if lat and lng:
        print(f"  ✓ Nominatim 成功")
        return lat, lng
    
    # 策略3: 提取简化地址重试 GSI
    if is_japanese:
        extracted = extract_address(original_address)
        if extracted != original_address and len(extracted) > 3:
            print(f"[3/4] GSI 简化地址: {extracted}")
            time.sleep(0.3)
            lat, lng = geocode_gsi(extracted, timeout=8)
            if lat and lng:
                print(f"  ✓ GSI 简化地址成功")
                return lat, lng
    
    # 策略4: Nominatim 全球搜索
    print(f"[4/4] Nominatim 全球: {address}, Japan")
    time.sleep(0.3)
    lat, lng = geocode_nominatim(address + ", Japan", country_code=None, timeout=8)
    if lat and lng:
        print(f"  ✓ Nominatim 全球成功")
        return lat, lng
    
    print(f"  ✗ 所有尝试失败: {address}")
    return None, None
