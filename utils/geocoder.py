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

def reverse_geocode_nominatim(lat: float, lng: float, timeout=8):
    """
    反向地理编码：经纬度 → 日文地址
    :param lat: 纬度
    :param lng: 经度
    :param timeout: 超时时间（秒）
    :return: 日文地址字符串；若失败，返回 None
    """
    url = "https://nominatim.openstreetmap.org/reverse"
    headers = {
        "User-Agent": "FCL-Checker/1.0 (https://github.com/your-repo)",
        "Accept-Language": "ja"  # 只要日文
    }
    
    params = {
        "lat": lat,
        "lon": lng,
        "format": "json",
        "addressdetails": 1,
        "zoom": 18  # 详细级别
    }
    
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=timeout)
        resp.raise_for_status()
        result = resp.json()
        
        if "address" in result:
            addr_parts = result["address"]
            parts = []
            
            # 调试：打印所有可用的地址组件
            print(f"  反向地理编码组件: {list(addr_parts.keys())}")
            
            # 都道府县（多种可能的字段名）
            prefecture = None
            for key in ["state", "province", "region", "ISO3166-2-lvl4"]:
                if key in addr_parts:
                    prefecture = addr_parts[key]
                    break
            
            # 如果都道府县是英文或ISO代码，转换为日文
            if prefecture:
                # ISO 3166-2 代码映射（47个都道府县）
                iso_map = {
                    "JP-01": "北海道", "JP-02": "青森県", "JP-03": "岩手県", "JP-04": "宮城県",
                    "JP-05": "秋田県", "JP-06": "山形県", "JP-07": "福島県", "JP-08": "茨城県",
                    "JP-09": "栃木県", "JP-10": "群馬県", "JP-11": "埼玉県", "JP-12": "千葉県",
                    "JP-13": "東京都", "JP-14": "神奈川県", "JP-15": "新潟県", "JP-16": "富山県",
                    "JP-17": "石川県", "JP-18": "福井県", "JP-19": "山梨県", "JP-20": "長野県",
                    "JP-21": "岐阜県", "JP-22": "静岡県", "JP-23": "愛知県", "JP-24": "三重県",
                    "JP-25": "滋賀県", "JP-26": "京都府", "JP-27": "大阪府", "JP-28": "兵庫県",
                    "JP-29": "奈良県", "JP-30": "和歌山県", "JP-31": "鳥取県", "JP-32": "島根県",
                    "JP-33": "岡山県", "JP-34": "広島県", "JP-35": "山口県", "JP-36": "徳島県",
                    "JP-37": "香川県", "JP-38": "愛媛県", "JP-39": "高知県", "JP-40": "福岡県",
                    "JP-41": "佐賀県", "JP-42": "長崎県", "JP-43": "熊本県", "JP-44": "大分県",
                    "JP-45": "宮崎県", "JP-46": "鹿児島県", "JP-47": "沖縄県"
                }
                
                # 英文名称映射
                name_map = {
                    "Tokyo": "東京都", "Osaka": "大阪府", "Kyoto": "京都府",
                    "Hokkaido": "北海道", "Kanagawa": "神奈川県", "Chiba": "千葉県",
                    "Saitama": "埼玉県", "Aichi": "愛知県", "Hyogo": "兵庫県",
                    "Fukuoka": "福岡県", "Miyagi": "宮城県", "Hiroshima": "広島県"
                }
                
                # 先尝试 ISO 代码，再尝试英文名称
                prefecture = iso_map.get(prefecture, name_map.get(prefecture, prefecture))
                parts.append(prefecture)
            
            # 市区町村
            if "city" in addr_parts:
                parts.append(addr_parts["city"])
            elif "town" in addr_parts:
                parts.append(addr_parts["town"])
            elif "village" in addr_parts:
                parts.append(addr_parts["village"])
            
            # 区
            if "city_district" in addr_parts:
                parts.append(addr_parts["city_district"])
            elif "suburb" in addr_parts:
                parts.append(addr_parts["suburb"])
            
            # 町丁目
            has_neighbourhood = False
            if "neighbourhood" in addr_parts:
                parts.append(addr_parts["neighbourhood"])
                has_neighbourhood = True
            elif "quarter" in addr_parts:
                parts.append(addr_parts["quarter"])
                has_neighbourhood = True
            
            # 街道（只在没有町丁目信息时添加）
            # 避免出现"深江浜町１７号線"这样的组合
            if "road" in addr_parts and not has_neighbourhood:
                road_name = addr_parts["road"]
                # 跳过纯数字的道路名（如"１７号線"）
                if not road_name.replace("号線", "").replace("号", "").strip().isdigit():
                    parts.append(road_name)
            
            # 门牌号
            if "house_number" in addr_parts:
                parts.append(addr_parts["house_number"])
            
            if parts:
                japanese_addr = "".join(parts)
                print(f"  反向地理编码结果: {japanese_addr}")
                return japanese_addr
        
        # 如果没有提取到，使用 display_name
        return result.get("display_name", None)
    except Exception as e:
        print(f"反向地理编码错误: {e}")
        return None


def translate_romaji_to_japanese(address: str):
    """
    将英文罗马字地名转换为日文
    :param address: 包含罗马字的地址
    :return: 转换后的地址
    """
    # 常见地名的罗马字到日文映射
    romaji_map = {
        # 千叶县地名
        'Moroto': '師戸',
        'Inzai': '印西',
        'Chiba': '千葉',
        'Funabashi': '船橋',
        'Shirai': '白井',
        # 兵庫県神戸市地名
        'Fukaehama': '深江浜',
        'Higashinada': '東灘',
        'Kobe': '神戸',
        # 其他常见地名
        'Tokyo': '東京',
        'Osaka': '大阪',
        'Kyoto': '京都',
        'Yokohama': '横浜',
        'Nagoya': '名古屋',
        'Fukuoka': '福岡',
        'Sapporo': '札幌',
        'Hiroshima': '広島',
        # 行政区划
        'shi': '市',
        'ken': '県',
        'ku': '区',
        'machi': '町',
        'cho': '町',
        'dori': '通',
    }
    
    translated = address
    for romaji, japanese in romaji_map.items():
        # 使用单词边界匹配，避免部分匹配
        import re
        pattern = r'\b' + re.escape(romaji) + r'\b'
        translated = re.sub(pattern, japanese, translated, flags=re.IGNORECASE)
    
    return translated


def geocode_nominatim(address: str, country_code="jp", timeout=8):
    """
    备用地理编码：使用 OpenStreetMap Nominatim API
    :param address: 地址字符串（支持日文或英文）
    :param country_code: 国家代码，默认 "jp"（日本）
    :param timeout: 超时时间（秒）
    :return: (lat, lng, japanese_address) 元组；若失败，返回 (None, None, None)
    """
    url = "https://nominatim.openstreetmap.org/search"
    headers = {
        "User-Agent": "FCL-Checker/1.0 (https://github.com/your-repo)",
        "Accept-Language": "ja,en"  # 优先返回日文
    }
    
    # 尝试将罗马字转换为日文
    japanese_address = translate_romaji_to_japanese(address)
    addresses_to_try = [address]
    if japanese_address != address:
        # 优先尝试日文地址
        addresses_to_try.insert(0, japanese_address)
        print(f"  尝试日文地址: {japanese_address}")
    
    # 循环尝试每个地址版本
    for addr_to_try in addresses_to_try:
        # 构建查询参数
        params = {
            "q": addr_to_try,
            "format": "json",
            "limit": 3,  # 增加到3个结果，选择最精确的
            "addressdetails": 1,
            "extratags": 1,  # 获取额外标签
            "namedetails": 1  # 获取名称详情
        }
        
        # 如果指定了国家代码，添加到参数中
        if country_code:
            params["countrycodes"] = country_code
        
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            if data and len(data) > 0:
                # 选择最精确的结果（优先选择有 house_number 的）
                result = None
                for item in data:
                    if "address" in item and "house_number" in item["address"]:
                        result = item
                        print(f"  找到精确门牌号: {item['address'].get('house_number')}")
                        break
                
                # 如果没有门牌号，使用第一个结果
                if not result:
                    result = data[0]
                
                lat = float(result["lat"])
                lng = float(result["lon"])
                
                # 尝试提取日文地址
                japanese_address = None
                if "address" in result:
                    addr_parts = result["address"]
                    # 构建日文地址（从大到小）
                    parts = []
                    
                    # 都道府县
                    if "state" in addr_parts:
                        parts.append(addr_parts["state"])
                    elif "province" in addr_parts:
                        parts.append(addr_parts["province"])
                    
                    # 市区町村
                    if "city" in addr_parts:
                        parts.append(addr_parts["city"])
                    elif "town" in addr_parts:
                        parts.append(addr_parts["town"])
                    elif "village" in addr_parts:
                        parts.append(addr_parts["village"])
                    
                    # 区
                    if "city_district" in addr_parts:
                        parts.append(addr_parts["city_district"])
                    elif "suburb" in addr_parts:
                        parts.append(addr_parts["suburb"])
                    
                    # 町丁目
                    if "neighbourhood" in addr_parts:
                        parts.append(addr_parts["neighbourhood"])
                    elif "quarter" in addr_parts:
                        parts.append(addr_parts["quarter"])
                    
                    # 街道
                    if "road" in addr_parts:
                        parts.append(addr_parts["road"])
                    
                    # 门牌号
                    if "house_number" in addr_parts:
                        parts.append(addr_parts["house_number"])
                    
                    if parts:
                        japanese_address = "".join(parts)
                
                # 如果地址不完整（少于3个组件），尝试反向地理编码获取更完整的地址
                if not japanese_address or len(japanese_address) < 10:
                    print(f"  地址不完整，尝试反向地理编码...")
                    reverse_addr = reverse_geocode_nominatim(lat, lng, timeout=timeout)
                    if reverse_addr:
                        japanese_address = reverse_addr
                
                # 如果还是没有，使用 display_name
                if not japanese_address:
                    japanese_address = result.get("display_name", None)
                
                return lat, lng, japanese_address
        except requests.exceptions.Timeout:
            print(f"  Nominatim 超时: {addr_to_try}")
            continue
        except requests.exceptions.RequestException as e:
            print(f"  Nominatim 网络错误: {e}")
            continue
        except Exception as e:
            print(f"  Nominatim 错误: {e}")
            continue
    
    # 所有尝试都失败
    return None, None, None


def normalize_address(address: str):
    """
    标准化日本地址格式
    例如：東京都中央区銀座4-6-16 → 東京都中央区銀座4丁目6-16
    """
    # 移除建筑物名称（在空格或全角空格后的内容）
    addr = re.sub(r'[　\s]+(.*?(ビル|タワー|マンション|階|F|内|近く|付近).*)$', '', address)
    
    # 转换 X-Y-Z 格式为 X丁目Y-Z（如果前面没有丁目）
    # 例如：銀座4-6-16 → 銀座4丁目6-16
    def add_chome(match):
        prefix = match.group(1)
        num1 = match.group(2)
        rest = match.group(3)
        # 检查前面是否已经有丁目
        if '丁目' not in prefix[-3:]:
            return f"{prefix}{num1}丁目{rest}"
        return match.group(0)
    
    addr = re.sub(r'([^\d丁目])(\d+)-(\d+[-\d]*)', add_chome, addr)
    
    return addr.strip()


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
    # 先标准化地址
    normalized = normalize_address(address)
    candidates = []
    
    # 添加标准化后的地址
    if normalized not in candidates:
        candidates.append(normalized)
    
    # 如果原地址不同，也添加
    if address != normalized and address not in candidates:
        candidates.append(address)
    
    # 基于标准化地址生成简化版本
    base_addr = normalized
    
    # 移除建筑物名称、楼层等
    addr = re.sub(r'[　\s]+.*?(ビル|タワー|マンション|階|F).*$', '', base_addr)
    if addr != base_addr and addr not in candidates:
        candidates.append(addr)
    
    # 移除番地号（1番地等）
    addr = re.sub(r'[0-9０-９]+番地?$', '', base_addr)
    if addr != base_addr and addr not in candidates:
        candidates.append(addr)
    
    # 移除最后的号码部分（-16、16号等）
    addr = re.sub(r'[-−ー][0-9０-９]+号?$', '', base_addr)
    if addr != base_addr and addr not in candidates:
        candidates.append(addr)
    
    # 只保留到丁目+第一个号码（例如：4丁目6）
    match = re.search(r'(.*?[0-9０-９]+丁目[0-9０-９]+)', base_addr)
    if match:
        addr = match.group(1)
        if addr not in candidates:
            candidates.append(addr)
    
    # 只保留到丁目
    match = re.search(r'(.*?[0-9０-９]+丁目)', base_addr)
    if match:
        addr = match.group(1)
        if addr not in candidates:
            candidates.append(addr)
    
    # 移除丁目后的所有内容
    addr = re.sub(r'[0-9０-９]+丁目.*$', '', base_addr)
    if addr != base_addr and len(addr) > 5 and addr not in candidates:
        candidates.append(addr)
    
    # 只保留到区/市/町/村
    match = re.search(r'(.*?[都道府県][^市区町村]+[市区町村])', base_addr)
    if match:
        addr = match.group(1)
        if addr not in candidates:
            candidates.append(addr)
    
    return candidates


def extract_postal_code(address: str):
    """
    从地址中提取日本邮编
    支持格式：689-3104, 〒689-3104, 6893104
    :return: 邮编字符串或 None
    """
    import re
    
    # 匹配日本邮编格式：XXX-XXXX 或 XXXXXXX
    patterns = [
        r'〒?\s*(\d{3}-\d{4})',  # 689-3104 或 〒689-3104
        r'\b(\d{7})\b',          # 6893104
    ]
    
    for pattern in patterns:
        match = re.search(pattern, address)
        if match:
            postal = match.group(1)
            # 标准化为 XXX-XXXX 格式
            if '-' not in postal:
                postal = f"{postal[:3]}-{postal[3:]}"
            return postal
    
    return None


def geocode_by_postal_code(postal_code: str, timeout=8):
    """
    使用邮编进行地理编码
    优先使用 GSI API，备用 Nominatim
    :param postal_code: 日本邮编（格式：XXX-XXXX）
    :return: (lat, lng, japanese_address) 或 (None, None, None)
    """
    # 方法1: 尝试 GSI API（日本国土地理院）
    try:
        gsi_url = "https://msearch.gsi.go.jp/address-search/AddressSearch"
        resp = requests.get(gsi_url, params={"q": postal_code}, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        
        if isinstance(data, list) and len(data) > 0:
            feature = data[0]
            if "geometry" in feature and "coordinates" in feature["geometry"]:
                coord = feature["geometry"]["coordinates"]
                lat = float(coord[1])
                lng = float(coord[0])
                
                # 提取日文地址
                japanese_address = None
                if "properties" in feature:
                    props = feature["properties"]
                    # GSI 返回完整的日文地址
                    if "title" in props:
                        japanese_address = props["title"]
                
                if japanese_address:
                    print(f"  GSI 邮编查询成功: {postal_code} → {japanese_address}")
                    return lat, lng, japanese_address
    except Exception as e:
        print(f"  GSI 邮编查询失败: {e}")
    
    # 方法2: 备用 Nominatim
    try:
        url = "https://nominatim.openstreetmap.org/search"
        headers = {
            "User-Agent": "FCL-Checker/1.0 (https://github.com/your-repo)",
            "Accept-Language": "ja"
        }
        
        # 尝试多种查询方式（必须限定在日本）
        queries = [
            {"q": f"{postal_code}, Japan", "countrycodes": "jp"},
            {"postalcode": postal_code, "countrycodes": "jp"},
        ]
        
        for params in queries:
            params.update({"format": "json", "limit": 1, "addressdetails": 1})
            
            resp = requests.get(url, params=params, headers=headers, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            
            if data and len(data) > 0:
                result = data[0]
                
                # 验证是否在日本
                if "address" in result:
                    country = result["address"].get("country_code", "").upper()
                    if country != "JP":
                        print(f"  跳过非日本结果: {country}")
                        continue
                
                lat = float(result["lat"])
                lng = float(result["lon"])
                
                # 提取日文地址
                japanese_address = None
                if "address" in result:
                    addr_parts = result["address"]
                    parts = []
                    
                    # 构建日文地址（按日本地址格式）
                    for key in ["state", "city", "town", "village", "city_district", "suburb", "neighbourhood", "quarter"]:
                        if key in addr_parts:
                            val = addr_parts[key]
                            # 转换 ISO 代码为日文
                            if key == "state" and val.startswith("JP-"):
                                iso_map = {
                                    "JP-31": "鳥取県", "JP-28": "兵庫県", "JP-13": "東京都",
                                    "JP-27": "大阪府", "JP-26": "京都府", "JP-01": "北海道"
                                }
                                val = iso_map.get(val, val)
                            parts.append(val)
                    
                    if parts:
                        japanese_address = "".join(parts)
                
                if not japanese_address:
                    japanese_address = result.get("display_name", None)
                
                if japanese_address:
                    print(f"  Nominatim 邮编查询成功: {postal_code} → {japanese_address}")
                    return lat, lng, japanese_address
        
        return None, None, None
    except Exception as e:
        print(f"  Nominatim 邮编查询失败: {e}")
        return None, None, None


def simplify_english_address(address: str):
    """
    简化英文日本地址
    例如：7F, KR GinzaⅡ, 2-15-2, Ginza, Chuo-Ku, Tokyo, 104-0061, Japan
    返回：["2-15-2 Ginza, Chuo-Ku, Tokyo, Japan", "Ginza, Chuo-Ku, Tokyo, Japan", ...]
    """
    import re
    
    candidates = [address]
    
    # 先提取邮编（日本邮编格式：XXX-XXXX，3位-4位）
    postal_match = re.search(r'\b(\d{3}-\d{4})\b', address)
    postal_code = postal_match.group(1) if postal_match else None
    
    # 如果没有找到标准邮编格式，尝试7位连续数字
    if not postal_code:
        postal_match = re.search(r'\b(\d{7})\b', address)
        if postal_match:
            postal_code = f"{postal_match.group(1)[:3]}-{postal_match.group(1)[3:]}"
    
    # 提取街道号码（排除邮编）
    # 街道号码通常是 1-4 位数字，不是 3-4 位的邮编格式
    street_number = None
    street_matches = re.findall(r'\b(\d{1,4}-\d{1,3}(?:-\d{1,3})?)\b', address)
    for match in street_matches:
        # 排除邮编格式（3位-4位）
        if not re.match(r'^\d{3}-\d{4}$', match):
            street_number = match
            break
    
    # 移除楼层信息（7F, 8th Floor等）和 NO. 前缀
    addr = re.sub(r'\bNO\.\s*|\b\d+F\b|\b\d+(st|nd|rd|th)\s+Floor\b', '', address, flags=re.IGNORECASE)
    addr = re.sub(r'\s+,\s+', ', ', addr).strip(', ')
    if addr != address and addr not in candidates:
        candidates.append(addr)
    
    # 构建简化的查询：主要地名 + 邮编
    # 例如：Yae, Daisen, Tottori 689-3104, Japan
    parts = [p.strip() for p in address.split(',')]
    main_locations = []
    
    for part in parts:
        # 从包含门牌号的部分提取地名（如 NO.822-1.YAE → YAE 或 2300 Moroto → Moroto）
        if re.search(r'\bNO\.\s*\d+-\d+\.?([A-Z]+)', part, re.IGNORECASE):
            # 提取门牌号后的地名
            match = re.search(r'\bNO\.\s*\d+-\d+\.?([A-Z]+)', part, re.IGNORECASE)
            if match:
                location_name = match.group(1)
                main_locations.append(location_name)
                continue
        
        # 提取 "数字 地名" 格式中的地名（如 "2300 Moroto" → "Moroto"）
        if re.search(r'^\d+\s+([A-Z][a-z]+)', part, re.IGNORECASE):
            match = re.search(r'^\d+\s+([A-Z][a-z]+)', part, re.IGNORECASE)
            if match:
                location_name = match.group(1)
                main_locations.append(location_name)
                continue
        
        # 提取 "门牌号 地名-MACHI/CHO" 格式（如 "109-1 FUKAEHAMA-MACHI" → "FUKAEHAMA-MACHI"）
        if re.search(r'^\d+-\d+\s+([A-Z]+-?(MACHI|CHO|DORI))', part, re.IGNORECASE):
            match = re.search(r'^\d+-\d+\s+([A-Z]+-?(MACHI|CHO|DORI))', part, re.IGNORECASE)
            if match:
                location_name = match.group(1)
                main_locations.append(location_name)
                continue
        
        # 跳过纯门牌号、楼层、邮编
        if re.search(r'^\d+F\b|^NO\.\s*\d+-\d+$|^\d{1,4}-\d{1,3}(?:-\d{1,3})?$|^\d{3}-\d{4}$|^\d{7}$', part, re.IGNORECASE):
            continue
        
        # 处理 DISTRICT, -KU, -MACHI, SHI, KEN 等行政区划后缀
        if re.search(r'\b(DISTRICT|PREFECTURE|COUNTY|SHI|KEN|KU)\b', part, re.IGNORECASE):
            # 提取主要地名（去除后缀）
            main_name = re.sub(r'\s+(DISTRICT|PREFECTURE|COUNTY|SHI|KEN|KU)\b', '', part, flags=re.IGNORECASE).strip()
            if main_name:
                main_locations.append(main_name)
        elif not re.search(r'\bJAPAN\b', part, re.IGNORECASE):
            main_locations.append(part)
    
    # 优先级策略：完整地址 > 地名组合 > 邮编查询
    # 这样可以避免邮编数据库不准确的问题
    
    # 如果有街道号码，优先构建：门牌号 + 主要地名（不带邮编）
    if street_number and main_locations:
        # 优先级1: 门牌号 + 所有地名（最精确）
        addr_with_number = f"{street_number}, " + ', '.join(main_locations) + ', Japan'
        if addr_with_number not in candidates:
            candidates.insert(1, addr_with_number)
        
        # 优先级2: 门牌号 + 最后2-3个地名
        if len(main_locations) >= 2:
            key_locations = main_locations[-2:]
            addr_short = f"{street_number}, " + ', '.join(key_locations) + ', Japan'
            if addr_short not in candidates:
                candidates.insert(2, addr_short)
    
    # 如果有地名，构建不带门牌号的地址
    if main_locations:
        # 优先级3: 所有地名（不带邮编）
        full_location = ', '.join(main_locations) + ', Japan'
        if full_location not in candidates:
            candidates.append(full_location)
        
        # 优先级4: 最后2-3个地名
        if len(main_locations) >= 2:
            key_locations = main_locations[-2:]
            simplified = ', '.join(key_locations) + ', Japan'
            if simplified not in candidates:
                candidates.append(simplified)
    
    # 最后才尝试邮编查询（因为邮编数据库可能不准确）
    if main_locations and postal_code:
        # 门牌号 + 地名 + 邮编
        if street_number:
            full_addr = f"{street_number}, " + ', '.join(main_locations) + f', {postal_code}, Japan'
            if full_addr not in candidates:
                candidates.append(full_addr)
        
        # 地名 + 邮编
        full_location_postal = ', '.join(main_locations) + f', {postal_code}, Japan'
        if full_location_postal not in candidates:
            candidates.append(full_location_postal)
    
    # 移除建筑物名称，但保留街道号码和地名
    parts = address.split(',')
    if len(parts) > 2:
        # 如果有街道号码，构建精确地址
        if street_number:
            # 收集所有有效的地名部分（跳过楼层、建筑物名称、门牌号）
            valid_parts = []
            for i, part in enumerate(parts):
                part = part.strip()
                # 跳过楼层和建筑物名称
                if re.search(r'^\d+F\b|ビル|タワー|Building|^KR\s|Ⅱ', part, re.IGNORECASE):
                    continue
                # 跳过包含街道号码的部分
                if street_number in part:
                    continue
                # 跳过邮编
                if re.search(r'^\d{3}-\d{4}$|^\d{7}$', part):
                    continue
                # 跳过 Japan
                if re.search(r'^JAPAN$', part, re.IGNORECASE):
                    continue
                # 保留其他部分
                if part:
                    valid_parts.append(part)
            
            # 构建：街道号码 + 有效地名
            if valid_parts:
                precise_addr = f"{street_number}, " + ', '.join(valid_parts) + ', Japan'
                if precise_addr not in candidates:
                    candidates.insert(1, precise_addr)  # 优先级高
        
        # 尝试从第二部分开始
        addr = ', '.join(parts[1:]).strip()
        if addr not in candidates:
            candidates.append(addr)
        
        # 尝试从第三部分开始（跳过街道号码）
        if len(parts) > 3:
            addr = ', '.join(parts[2:]).strip()
            if addr not in candidates:
                candidates.append(addr)
    
    # 提取主要地名（Ginza, Chuo-Ku, Tokyo等）
    # 查找包含 Tokyo, Osaka, Kyoto 等城市名的部分
    major_cities = ['Tokyo', 'Osaka', 'Kyoto', 'Yokohama', 'Nagoya', 'Kobe', 'Fukuoka', 'Sapporo']
    for city in major_cities:
        if city in address:
            # 找到城市名后的所有内容
            idx = address.find(city)
            addr = address[idx:].strip()
            if addr not in candidates:
                candidates.append(addr)
            
            # 只保留城市名 + Japan
            addr = f"{city}, Japan"
            if addr not in candidates:
                candidates.append(addr)
    
    return candidates


def geocode(address: str):
    """
    智能地理编码：优先邮编，然后 GSI，支持地址降级策略
    如果详细地址找不到，自动尝试简化版本
    :param address: 地址字符串（日文或英文）
    :return: (lat, lng, used_address) 元组；若失败，返回 (None, None, None)
            used_address 是实际用于解析的地址（英文输入时返回日文地址）
    """
    original_address = address
    
    # 策略0: 检测邮编但不单独使用，而是结合地址信息
    postal_code = extract_postal_code(address)
    postal_result = None
    
    # 如果有邮编，优先尝试"地址 + 邮编"的组合查询
    # 而不是单独使用邮编（避免邮编数据库错误）
    if postal_code and False:  # 暂时禁用单独邮编查询
        print(f"检测到邮编: {postal_code}")
        lat, lng, japanese_addr = geocode_by_postal_code(postal_code, timeout=6)
        if lat and lng:
            # 尝试使用反向地理编码获取更完整的地址
            reverse_addr = reverse_geocode_nominatim(lat, lng, timeout=6)
            if reverse_addr and len(reverse_addr) > len(japanese_addr or ""):
                japanese_addr = reverse_addr
                
                # 去除重复的町名（如：深江浜町深江浜町 → 深江浜町）
                # 查找重复的町名模式
                japanese_addr = re.sub(r'([^市区町村]{2,}町)\1', r'\1', japanese_addr)
                
                print(f"  使用反向地理编码获取完整地址: {japanese_addr}")
            
            # 验证邮编结果是否合理：检查地址中的地名是否匹配
            # 提取原地址中的主要地名（城市、区等）
            address_upper = address.upper()
            location_keywords = []
            
            # 提取可能的地名关键词
            for part in address.split(','):
                part = part.strip().upper()
                # 跳过邮编、门牌号、国家名
                if re.search(r'\d{3}-?\d{4}|^\d+-\d+|JAPAN', part):
                    continue
                # 移除 NO., -KU, -MACHI 等后缀
                part = re.sub(r'\bNO\.\s*|\b-?(KU|MACHI|CHO|SHI|GUN)\b', '', part).strip()
                if len(part) > 2:
                    location_keywords.append(part)
            
            # 检查日文地址是否包含这些关键词的日文翻译
            # 简单验证：如果原地址包含 TOTTORI，日文地址应该包含 鳥取
            location_map = {
                # 都道府県
                'TOTTORI': '鳥取', 'CHIBA': '千葉', 'TOKYO': '東京', 'OSAKA': '大阪',
                'KYOTO': '京都', 'KANAGAWA': '神奈川', 'AICHI': '愛知', 'HYOGO': '兵庫',
                'FUKUOKA': '福岡', 'HOKKAIDO': '北海道', 'MIYAGI': '宮城',
                # 市区町村
                'KOBE': '神戸', 'YOKOHAMA': '横浜', 'NAGOYA': '名古屋',
                'INZAI': '印西', 'SHIRAI': '白井', 'FUNABASHI': '船橋',
                'DAISEN': '大山', 'SAIHAKU': '西伯', 'HIGASHINADA': '東灘',
                # 町名
                'FUKAEHAMA': '深江浜', 'MOROTO': '師戸'
            }
            
            is_valid = False
            for keyword in location_keywords:
                if keyword in location_map:
                    japanese_keyword = location_map[keyword]
                    if japanese_keyword in (japanese_addr or ''):
                        is_valid = True
                        break
            
            # 如果没有找到匹配的关键词，可能是邮编查询返回了错误位置
            if not is_valid and location_keywords:
                print(f"  ⚠️ 邮编查询结果可能不准确（地名不匹配），将尝试完整地址查询")
                postal_result = None  # 不使用邮编结果
            else:
                # 如果地址中有门牌号，尝试添加到日文地址中（排除邮编）
                if japanese_addr:
                    street_matches = re.findall(r'\b(\d{1,4}-\d{1,3}(?:-\d{1,3})?)\b', address)
                    for street_number in street_matches:
                        # 排除邮编格式（3位-4位）
                        if re.match(r'^\d{3}-\d{4}$', street_number):
                            continue
                        # 检查日文地址中是否已经包含门牌号
                        if street_number not in japanese_addr:
                            # 将门牌号添加到日文地址末尾
                            japanese_addr = f"{japanese_addr}{street_number}"
                            print(f"  添加门牌号: {street_number}")
                            break
                
                print(f"  ✓ 邮编查询成功")
                postal_result = (lat, lng, japanese_addr if japanese_addr else original_address)
        
        time.sleep(0.3)
    
    # 如果邮编查询成功且验证通过，直接返回
    if postal_result:
        return postal_result
    
    # 检查是否为日文地址
    is_japanese = any('\u3040' <= c <= '\u309F' or  # 平假名
                     '\u30A0' <= c <= '\u30FF' or  # 片假名
                     '\u4E00' <= c <= '\u9FFF'     # 汉字
                     for c in address)
    
    # 生成地址候选列表（从详细到简略）
    if is_japanese:
        address_candidates = simplify_address(address)
        print(f"日文地址候选: {len(address_candidates)} 个")
    else:
        address_candidates = simplify_english_address(address)
        print(f"英文地址候选: {len(address_candidates)} 个")
    
    # 策略1: 逐级尝试 GSI（日本国土地理院，仅日文）
    if is_japanese:
        for i, addr in enumerate(address_candidates, 1):
            print(f"[GSI {i}/{len(address_candidates)}] {addr}")
            lat, lng = geocode_gsi(addr, timeout=6)
            if lat and lng:
                if addr != original_address:
                    print(f"  ✓ 使用简化地址成功: {addr}")
                else:
                    print(f"  ✓ 成功")
                return lat, lng, addr
            time.sleep(0.2)
    
    # 策略2: 逐级尝试 Nominatim（所有候选地址）
    for i, addr in enumerate(address_candidates, 1):
        print(f"[Nominatim {i}/{len(address_candidates)}] {addr}")
        lat, lng, japanese_addr = geocode_nominatim(addr, country_code="jp", timeout=6)
        if lat and lng:
            # 如果输入是英文，返回日文地址；如果输入是日文，返回简化后的地址
            used_address = japanese_addr if (japanese_addr and not is_japanese) else addr
            
            # 如果是英文地址且有日文地址，尝试添加门牌号（排除邮编）
            if not is_japanese and japanese_addr:
                street_number = None
                
                # 方法1: 提取 X-X-X 格式的门牌号
                street_matches = re.findall(r'\b(\d{1,4}-\d{1,3}(?:-\d{1,3})?)\b', original_address)
                for match in street_matches:
                    # 排除邮编格式（3位-4位）
                    if re.match(r'^\d{3}-\d{4}$', match):
                        continue
                    street_number = match
                    break
                
                # 方法2: 如果没有找到 X-X 格式，尝试提取 "数字 地名" 格式中的数字（如 "2300 Moroto"）
                if not street_number:
                    pure_number_match = re.search(r'\b(\d{1,4})\s+[A-Za-z]', original_address)
                    if pure_number_match:
                        street_number = pure_number_match.group(1)
                
                # 添加门牌号到日文地址
                if street_number and street_number not in japanese_addr:
                    used_address = f"{japanese_addr}{street_number}"
                    print(f"  添加门牌号到日文地址: {street_number}")
            
            if addr != original_address:
                print(f"  ✓ 使用简化地址成功: {addr}")
            else:
                print(f"  ✓ 成功")
            return lat, lng, used_address
        time.sleep(0.3)
    
    # 策略3: Nominatim 全球搜索（最后尝试）
    print(f"[Nominatim 全球] {original_address}")
    lat, lng, japanese_addr = geocode_nominatim(original_address, country_code=None, timeout=6)
    if lat and lng:
        print(f"  ✓ Nominatim 全球成功")
        # 如果输入是英文且获取到日文地址，返回日文地址
        used_address = japanese_addr if (japanese_addr and not is_japanese) else original_address
        
        # 如果是英文地址且有日文地址，尝试添加门牌号（排除邮编）
        if not is_japanese and japanese_addr:
            street_number = None
            
            # 方法1: 提取 X-X-X 格式的门牌号
            street_matches = re.findall(r'\b(\d{1,4}-\d{1,3}(?:-\d{1,3})?)\b', original_address)
            for match in street_matches:
                # 排除邮编格式（3位-4位）
                if re.match(r'^\d{3}-\d{4}$', match):
                    continue
                street_number = match
                break
            
            # 方法2: 如果没有找到 X-X 格式，尝试提取 "数字 地名" 格式中的数字（如 "2300 Moroto"）
            if not street_number:
                pure_number_match = re.search(r'\b(\d{1,4})\s+[A-Za-z]', original_address)
                if pure_number_match:
                    street_number = pure_number_match.group(1)
            
            # 添加门牌号到日文地址
            if street_number and street_number not in japanese_addr:
                used_address = f"{japanese_addr}{street_number}"
                print(f"  添加门牌号到日文地址: {street_number}")
        
        return lat, lng, used_address
    
    print(f"  ✗ 所有尝试失败: {original_address}")
    return None, None, None
