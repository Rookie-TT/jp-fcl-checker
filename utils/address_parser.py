# utils/address_parser.py
# 功能：使用 japanese-address-parser-py 库解析日本地址（NLP 集成）
# 支持提取：都道府县、市区町村、丁目番地等
# 作者：Grok AI 基于用户需求生成

from jp_address_parser import parse  # NLP 地址解析库

def parse_jp_address(address: str) -> dict:
    """
    解析日本地址，返回结构化数据。
    :param address: 输入的日本地址字符串（如 "神奈川県横浜市鶴見区大黒ふ頭1-2-3"）
    :return: 字典，包含 full（原地址）、prefecture（都道府县）、city（市区）、town（町村）、rest（剩余部分）
    """
    try:
        result = parse(address)
        return {
            "full": address.strip(),
            "prefecture": result.prefecture or "",
            "city": result.city or "",
            "town": result.town or "",
            "rest": result.rest or ""
        }
    except Exception as e:
        print(f"地址解析错误: {e}")  # 日志记录
        return {"full": address.strip(), "prefecture": "", "city": "", "town": "", "rest": ""}