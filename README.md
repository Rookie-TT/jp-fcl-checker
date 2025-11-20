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


## Vercel 部署

### 快速部署

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/your-username/jp-fcl-checker)

### 手动部署步骤

1. **安装 Vercel CLI**
```bash
npm install -g vercel
```

2. **登录 Vercel**
```bash
vercel login
```

3. **部署项目**
```bash
# 预览部署
vercel

# 生产部署
vercel --prod
```

或者使用提供的部署脚本：
```bash
# Windows
deploy.bat

# Linux/Mac
chmod +x deploy.sh
./deploy.sh
```

### 通过 Vercel 网站部署

1. 访问 [Vercel](https://vercel.com)
2. 点击 "Add New Project"
3. 导入你的 Git 仓库
4. Vercel 会自动检测配置并部署
5. 获取部署 URL

详细部署说明请查看 [DEPLOYMENT.md](DEPLOYMENT.md)

## 项目结构

```
jp-fcl-checker-master/
├── api/
│   └── index.py              # Flask 应用入口
├── config/
│   └── ports.yaml            # 港口配置数据
├── templates/
│   └── index.html            # 前端页面（日文）
├── utils/
│   ├── geocoder.py           # 地理编码（GSI + Nominatim）
│   ├── osm_roads.py          # OSM 道路查询
│   ├── rules.py              # FCL 可达性规则
│   ├── address_extractor.py  # 地址提取工具
│   └── jp_address_parser_simple.py  # 日本地址解析
├── vercel.json               # Vercel 配置
├── requirements.txt          # Python 依赖
├── run.py                    # 本地开发启动脚本
└── DEPLOYMENT.md             # 详细部署文档
```

## API 接口

### POST /check

检查地址的 FCL 可达性

**请求体：**
```json
{
  "addresses": [
    "北海道雨竜郡北竜町",
    "神奈川県横浜市鶴見区大黒ふ頭1-2-3"
  ]
}
```

**响应：**
```json
{
  "results": [
    {
      "address": "北海道雨竜郡北竜町",
      "can_access": true,
      "reason": "道路幅員3.5m以上",
      "nearest_port": "苫小牧港（JPTKM）",
      "distance": "約120km",
      "estimated_time": "予想牽引時間：4時間"
    }
  ]
}
```

## 技术栈

- **后端**: Flask 3.0.3
- **地理编码**: 
  - 日本国土地理院 API (GSI)
  - OpenStreetMap Nominatim API
- **道路数据**: OpenStreetMap Overpass API
- **部署**: Vercel Serverless Functions
- **前端**: HTML + JavaScript (原生)

## 环境要求

- Python 3.9+
- 网络连接（访问外部 API）

## 配置说明

### 港口配置 (config/ports.yaml)

```yaml
destination_ports:
  - name: 東京港
    code: JPTYO
    lat: 35.6329
    lng: 139.7677
  # ... 更多港口
```

### 地理编码

系统使用多层地理编码策略：
1. 优先使用日本国土地理院 API (GSI)
2. 失败时使用 OpenStreetMap Nominatim
3. 自动提取地址部分（去除建筑物名称）

### 道路规则

- 道路宽度 >= 3.5m
- 支持黑白名单配置
- 自动查询 OSM 道路数据

## 使用建议

1. **地址格式**：
   - ✓ 推荐：`北海道札幌市中央区○○町1-2-3`
   - ✓ 可用：`札幌市`、`Sapporo, Hokkaido`
   - ✗ 避免：具体建筑物名称（如商店、学校名）

2. **批量查询**：
   - 每行一个地址
   - 支持多行输入

3. **性能**：
   - 首次查询可能较慢（冷启动）
   - 地理编码 API 有速率限制

## 常见问题

### Q: 为什么某些地址返回"座標解析不可"？

A: 可能原因：
- 地址过于模糊（如只有建筑物名称）
- 地理编码 API 数据库中没有该地址
- 网络连接问题

建议使用完整的街道地址或城市名。

### Q: 如何添加新的港口？

A: 编辑 `config/ports.yaml`，添加港口信息：
```yaml
- name: 新港口名
  code: JPXXX
  lat: 纬度
  lng: 经度
```

### Q: 部署到 Vercel 后超时？

A: Vercel 免费版有 10 秒执行时间限制。如果地理编码 API 响应慢，考虑：
- 优化超时设置
- 使用缓存
- 升级 Vercel 套餐

## 开发

### 本地开发

```bash
# 克隆项目
git clone <repository-url>
cd jp-fcl-checker-master

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 运行开发服务器
python run.py
```

### 测试

```bash
# 测试地理编码
python test_geocode.py

# 测试特定地址
python test_address.py
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

如有问题，请提交 GitHub Issue。
