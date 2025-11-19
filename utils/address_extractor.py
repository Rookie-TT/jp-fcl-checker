#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
地址提取工具：从包含建筑物名称的字符串中提取地址部分
"""
import re

def extract_address(text: str) -> str:
    """
    从文本中提取地址部分
    :param text: 包含地址的文本（可能包含建筑物名称）
    :return: 提取的地址字符串
    """
    # 日本地址关键词
    prefectures = [
        "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
        "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
        "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県",
        "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
        "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
        "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
        "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県"
    ]
    
    # 尝试匹配都道府県开头的地址
    for pref in prefectures:
        if pref in text:
            # 找到都道府県的位置，从这里开始提取
            idx = text.index(pref)
            # 提取从都道府県开始到第一个空格、括号或特殊字符之前的部分
            addr_part = text[idx:]
            # 移除常见的建筑物标识
            addr_part = re.split(r'[\s　(（]', addr_part)[0]
            return addr_part
    
    # 如果没有找到都道府県，尝试匹配市区町村
    city_pattern = r'([^\s　]+?[市区町村郡])'
    match = re.search(city_pattern, text)
    if match:
        return match.group(1)
    
    # 如果都没找到，返回原文本
    return text


def suggest_address_format(text: str) -> str:
    """
    为用户提供地址格式建议
    :param text: 用户输入的文本
    :return: 建议的地址格式
    """
    # 检测是否包含建筑物名称关键词
    building_keywords = ["店", "ビル", "マンション", "アパート", "ホテル", "学校", "病院", "公園"]
    
    has_building = any(keyword in text for keyword in building_keywords)
    
    if has_building:
        extracted = extract_address(text)
        if extracted != text:
            return f"建议使用地址部分：{extracted}"
        else:
            return "建议使用完整的街道地址，例如：東京都渋谷区○○町1-2-3"
    
    return ""
