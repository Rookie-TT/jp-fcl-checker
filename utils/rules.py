# utils/rules.py
# 功能：FCL 可达性规则引擎（含黑白名单）
# 判断逻辑：道路宽度 >= 3.5m + 黑名单（古街/步行街） + 白名单（工业区）

import yaml
import os

def load_ports():
    """加载港口配置（从 YAML）。"""
    with open("config/ports.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)["destination_ports"]

def is_restricted_area(parsed):
    """检查是否在限制区域（黑名单）。"""
    # 黑名单：古街/商业区，无法进入集装箱车
    restricted = ["東山区", "祇園", "銀座", "谷中", "国際通り"]
    text = (parsed["city"] + parsed["town"] + parsed["rest"])
    return any(area in text for area in restricted)

def can_access_fcl(roads, parsed):
    """
    判断是否可收整箱。
    :param roads: OSM 道路列表
    :param parsed: 解析后的地址
    :return: (bool, str) - (可达, 日文理由)
    """
    # 白名单：已知工业/港口区
    if any(wh in parsed["town"] + parsed["city"] for wh in ["大黒ふ頭", "鶴見区"]):
        return True, "港湾工業地区に位置、道路幅12m以上、40HQ対応可能"
    
    # 黑名单检查
    if is_restricted_area(parsed):
        return False, "祇園/銀座などの古街/商業歩行街、コンテナ車進入不可"
    
    if not roads:
        return False, "道路データなし、確認必要"
    
    # 过滤无效道路类型（步行街等）
    valid_roads = [r for r in roads if r["type"] not in ["living_street", "pedestrian", "footway"]]
    if not valid_roads:
        return False, "歩行街のみ、コンテナ車進入不可"
    
    min_width = min(r["width"] for r in valid_roads)
    if min_width < 3.5:
        return False, f"最近道路幅{min_width}m、コンテナ車進入不可"
    
    return True, f"道路幅{min_width}m以上、40HQ対応可能"