# Vercel 部署指南

## 前置要求

1. 注册 Vercel 账号：https://vercel.com
2. 安装 Vercel CLI（可选）：`npm install -g vercel`

## 部署步骤

### 方法 1：通过 Vercel 网站部署（推荐）

1. 登录 Vercel：https://vercel.com/login
2. 点击 "Add New Project"
3. 导入你的 Git 仓库（GitHub/GitLab/Bitbucket）
4. Vercel 会自动检测到 `vercel.json` 配置
5. 点击 "Deploy" 开始部署
6. 等待部署完成，获取部署 URL

### 方法 2：通过 Vercel CLI 部署

```bash
# 安装 Vercel CLI
npm install -g vercel

# 登录
vercel login

# 部署（在项目根目录执行）
vercel

# 生产环境部署
vercel --prod
```

## 项目结构

```
jp-fcl-checker-master/
├── api/
│   └── index.py          # Flask 应用入口
├── config/
│   └── ports.yaml        # 港口配置
├── templates/
│   └── index.html        # 前端页面
├── utils/
│   ├── geocoder.py       # 地理编码
│   ├── osm_roads.py      # OSM 道路查询
│   ├── rules.py          # FCL 规则判断
│   ├── address_extractor.py  # 地址提取
│   └── jp_address_parser_simple.py  # 日本地址解析
├── vercel.json           # Vercel 配置
├── requirements.txt      # Python 依赖
└── .vercelignore         # 忽略文件配置
```

## 配置说明

### vercel.json

- `builds`: 指定构建配置，使用 `@vercel/python` 构建器
- `routes`: 路由配置，所有请求转发到 `api/index.py`
- `env`: 环境变量，设置 `PYTHONPATH` 确保模块导入正确

### requirements.txt

包含所有必需的 Python 依赖：
- Flask: Web 框架
- Jinja2: 模板引擎
- PyYAML: YAML 配置文件解析
- requests: HTTP 请求库

## 环境变量（可选）

如果需要配置环境变量，在 Vercel 项目设置中添加：

1. 进入项目 Settings
2. 选择 Environment Variables
3. 添加需要的变量

## 本地测试

部署前建议本地测试：

```bash
# 激活虚拟环境
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 运行应用
python run.py

# 访问
http://localhost:5000
```

## 常见问题

### 1. 模块导入错误

确保 `vercel.json` 中设置了 `PYTHONPATH`：
```json
"env": {
  "PYTHONPATH": "."
}
```

### 2. 静态文件 404

确保 `templates` 目录在项目根目录，Flask 配置正确：
```python
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
app = Flask(__name__, template_folder=TEMPLATE_DIR)
```

### 3. API 超时

Vercel Serverless Functions 有 10 秒执行时间限制（免费版）。
如果地理编码 API 响应慢，考虑：
- 优化超时设置
- 使用缓存
- 升级 Vercel 套餐

### 4. 冷启动慢

Serverless 函数首次调用会有冷启动延迟，这是正常现象。
可以考虑：
- 使用 Vercel Pro 套餐减少冷启动
- 优化依赖大小

## 部署后验证

1. 访问部署 URL
2. 测试地址查询功能：
   - 输入：`北海道雨竜郡北竜町`
   - 输入：`神奈川県横浜市鶴見区大黒ふ頭1-2-3`
3. 检查 API 响应：
   - POST `/check` 接口
   - 返回 JSON 格式结果

## 更新部署

### 自动部署（推荐）

连接 Git 仓库后，每次 push 到主分支会自动触发部署。

### 手动部署

```bash
vercel --prod
```

## 监控和日志

1. 登录 Vercel Dashboard
2. 选择项目
3. 查看 Deployments 和 Functions 日志
4. 监控请求量和错误率

## 性能优化建议

1. **启用缓存**：对地理编码结果进行缓存
2. **压缩响应**：启用 gzip 压缩
3. **CDN 加速**：Vercel 自动提供全球 CDN
4. **异步处理**：对于批量查询，考虑异步处理

## 成本估算

Vercel 免费套餐限制：
- 100 GB 带宽/月
- 100 小时 Serverless 执行时间/月
- 无限部署次数

对于中小型应用，免费套餐通常足够。

## 技术支持

- Vercel 文档：https://vercel.com/docs
- Flask 文档：https://flask.palletsprojects.com/
- 项目问题：提交 GitHub Issue
