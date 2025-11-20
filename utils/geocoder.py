# utils/geocoder.py
# 功能：使用日本国土地理院（GSI）API 进行地理编码（免费，NLP/地图集成）
# 将地址转为经纬度（Lat, Lng）
# API 文档：https://msearch.gsi.go.jp/address-search/AddressSearch

import requests
import time
import re
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


def simplify_address(address: str):
    """
    逐步简化日本地址，生成多个候选地址
    例如：神奈川県横浜市鶴見区大黒ふ頭2丁目1番地
    返回：[
        "神奈川県横浜市鶴見区大黒ふ頭2丁目1番地",
        "神奈川県横浜市鶴見区大黒ふ頭2丁目",
        "神奈川県横浜市鶴見区大黒ふ頭",
        "神奈川県横浜市鶴見区",
    ]
    """
    candidates = [address]
    
    # 移除建筑物名称、楼层等
    addr = re.sub(r'[　\s]+.*?(ビル|タワー|マンション|階|F).*$', '', address)
    if addr != address and addr not in candidates:
        candidates.append(addr)
    
    # 移除番地号（1番地、1-2-3等）
    addr = re.sub(r'[0-9０-９]+番地?$', '', address)
    if addr != address and addr not in candidates:
        candidates.append(addr)
    
    # 移除详细号码（1-2-3、1丁目2番3号等）
    addr = re.sub(r'[0-9０-９\-−ー]+号?$', '', address)
    if addr != address and addr not in candidates:
        candidates.append(addr)
    
    # 移除番号（2番、3番等）
    addr = re.sub(r'[0-9０-９]+番$', '', address)
    if addr != address and addr not in candidates:
        candidates.append(addr)
    
    # 只保留到丁目
    match = re.search(r'(.*?[0-9０-９]+丁目)', address)
    if match:
        addr = match.group(1)
        if addr not in candidates:
            candidates.append(addr)
    
    # 移除丁目后的所有内容
    addr = re.sub(r'[0-9０-９]+丁目.*$', '', address)
    if addr != address and len(addr) > 5 and addr not in candidates:
        candidates.append(addr)
    
    # 只保留到区/市/町/村
    match = re.search(r'(.*?[都道府県][^市区町村]+[市区町村])', address)
    if match:
        addr = match.group(1)
        if addr not in candidates:
            candidates.append(addr)
    
    return candidates


def geocode(address: str):
    """
    智能地理编码：优先 GSI，支持地址降级策略
    如果详细地址找不到，自动尝试简化版本
    :param address: 地址字符串（日文或英文）
    :return: (lat, lng) 元组；若失败，返回 (None, None)
    """
    original_address = address
    
    # 检查是否为日文地址
    is_japanese = any('\u3040' <= c <= '\u309F' or  # 平假名
                     '\u30A0' <= c <= '\u30FF' or  # 片假名
                     '\u4E00' <= c <= '\u9FFF'     # 汉字
                     for c in address)
    
    # 生成地址候选列表（从详细到简略）
    if is_japanese:
        address_candidates = simplify_address(address)
        print(f"地址候选: {len(address_candidates)} 个")
    else:
        address_candidates = [address]
    
    # 策略1: 逐级尝试 GSI（日本国土地理院）
    if is_japanese:
        for i, addr in enumerate(address_candidates, 1):
            print(f"[GSI {i}/{len(address_candidates)}] {addr}")
            lat, lng = geocode_gsi(addr, timeout=6)
            if lat and lng:
                if addr != original_address:
                    print(f"  ✓ 使用简化地址成功: {addr}")
                else:
                    print(f"  ✓ 成功")
                return lat, lng
            time.sleep(0.2)
    
    # 策略2: 尝试 Nominatim（原始地址）
    print(f"[Nominatim] {original_address}")
    lat, lng = geocode_nominatim(original_address, country_code="jp", timeout=6)
    if lat and lng:
        print(f"  ✓ Nominatim 成功")
        return lat, lng
    
    # 策略3: Nominatim 全球搜索
    if is_japanese:
        print(f"[Nominatim 全球] {original_address}, Japan")
        time.sleep(0.3)
        lat, lng = geocode_nominatim(original_address + ", Japan", country_code=None, timeout=6)
        if lat and lng:
            print(f"  ✓ Nominatim 全球成功")
            return lat, lng
    
    print(f"  ✗ 所有尝试失败: {original_address}")
    return None, None
