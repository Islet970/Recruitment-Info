# Recruitment Info Platform

招聘信息聚合与数据分析平台。爬取牛客网招聘数据，提供可视化仪表盘、职位检索、简历分析、智能推荐等功能。

## 技术栈

| 层 | 技术 |
|---|---|
| **前端** | Next.js 16 + React 19 + TypeScript + Tailwind CSS 4 |
| **状态/数据** | Zustand + TanStack React Query + Axios |
| **图表** | ECharts 5 (echarts-for-react, echarts-wordcloud) |
| **后端** | FastAPI + SQLAlchemy 2.0 + MySQL 8.0 |
| **迁移** | Alembic |
| **爬虫** | Python (requests + aiohttp + parsel) |

## 项目结构

```
├── frontend/            # Next.js 前端
│   └── src/
│       ├── app/         # 页面路由
│       ├── components/  # 通用组件
│       ├── hooks/       # 自定义 Hooks
│       ├── lib/         # 工具函数
│       ├── store/       # Zustand 状态
│       └── types/       # TypeScript 类型
├── backend/             # FastAPI 后端
│   └── app/
│       ├── api/         # API 路由（auth, positions, companies, dashboard...）
│       ├── core/        # 配置、数据库连接
│       ├── models/      # SQLAlchemy 模型
│       ├── schemas/     # Pydantic 校验
│       └── services/    # 业务逻辑
├── output/              # 爬虫输出数据（JSON）
└── nowcoder_full_crawler.py  # 牛客网爬虫
```

## API 概览

| 前缀 | 功能 |
|---|---|
| `/api/auth` | 注册、登录、Token 刷新 |
| `/api/positions` | 职位列表、详情、相似推荐 |
| `/api/companies` | 公司列表、详情、规模/行业分类 |
| `/api/dashboard` | 数据统计、薪资分布、技能词云、趋势 |
| `/api/resumes` | 简历上传、管理 |
| `/api/analysis` | 简历分析（AI） |
| `/api/recommendations` | 职业路径、职位推荐 |
| `/api/categories` / `/api/skills` | 分类与技能数据 |
| `/api/users` | 个人信息、收藏管理 |

## 快速启动

### 后端

```bash
# 1. 创建 MySQL 数据库
mysql -u root -p -e "CREATE DATABASE recruitment_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，修改 DB_PASSWORD 为自己的 MySQL 密码

# cd backend/app/core 修改config
DB_PASSWORD: str = "在这里输入你的密码"

# 3.导入数据cd backend/scripts
python import_data.py
python create_views.py
python classify_positions.py

# 4.安装依赖
pip install -r requirements.txt

# 5. 启动
cd backend
uvicorn app.main:app --reload[ --host 0.0.0.0 --port 8000]
# API 地址: http://localhost:8000
# 文档:     http://localhost:8000/docs
```

### 前端

```bash
cd frontend
npm install
npm run dev
# 访问: http://localhost:3000
```

### 爬虫（可选）

```bash
# 在项目根目录
python nowcoder_full_crawler.py
# 数据输出至 output/ 目录
# 导入数据库: python backend/scripts/import_data.py
```

## 功能特性

- **多维度仪表盘**: 薪资分布、技能词云、学历/经验薪资分析、热门公司排行
- **职位检索与筛选**: 按分类、技能、薪资范围、学历要求筛选
- **公司百科**: 查看公司详细介绍、在招职位
- **简历管理**: 上传简历、AI 分析匹配度
- **智能推荐**: 基于简历和偏好的职位/职业路径推荐