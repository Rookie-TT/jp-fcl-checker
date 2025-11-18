# 日本地址 FCL 可达性检查工具

这是一个基于 Flask 的 Web 工具，用于货代公司检查日本地址是否可收整箱（FCL）。输入地址后，自动使用 NLP 解析 + 地图 API 判断道路可达性，并推荐最近港口。

## 功能
- **地址解析**：NLP 提取行政区、番地等。
- **地图集成**：国土地理院 Geocoding + OSM 道路查询。
- **规则判断**：黑白名单 + 道路宽度（>=3.5m）。
- **港口推荐**：距离计算 + 拖车时间估算。
- **批量支持**：前台多行输入，一键处理。
- **输出**：全日文界面 + 结果。

jp-fcl-checker/
├── app.py                     # ← 中文注释（后台逻辑）
├── config/ports.yaml          # ← 中文注释 + 日本港口数据
├── templates/index.html       # ← 完全日文界面 + 批量输入支持
├── utils/
│   ├── address_parser.py      # ← 中文注释
│   ├── geocoder.py            # ← 中文注释（国土地理院API）
│   ├── osm_roads.py           # ← 中文注释
│   └── rules.py               # ← 中文注释（含黑白名单规则）
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md                  # ← 默认中文（含部署步骤）

## 部署步骤

### 1. 本地运行（开发测试）
```bash
# 安装依赖
pip install -r requirements.txt

# 启动
python app.py

# 浏览器访问
http://localhost:5000