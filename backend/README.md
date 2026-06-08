# Recruitment Platform - Backend
FastAPI + SQLAlchemy 2.0 + MySQL

## Prerequisites
- Python 3.10+
- MySQL 8.0+

## Setup

### 1. 创建数据库
```sql
CREATE DATABASE recruitment_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env，修改 DB_PASSWORD 为你的 MySQL 密码
```

### 3. 安装依赖
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. 初始化数据库表
```bash
# 数据库表会由 SQLAlchemy 在首次启动时自动创建
# 如需手动执行迁移：
alembic upgrade head
```

## Run
```bash
uvicorn app.main:app --reload
```
