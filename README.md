# 恶意流量监控平台

这是一个最小可运行的演示版恶意流量监控项目，技术栈包括：

- 前端：Vue 3 + Vite + Element Plus + ECharts
- 后端：Flask + Flask-SocketIO + SQLAlchemy
- 数据库：MySQL 8
- 消息队列：Kafka

## 目录说明

- `frontend/`：前端项目
- `backend/`：后端接口、WebSocket、数据模型
- `scripts/`：数据库初始化、模拟数据导入、Kafka 脚本
- `docker/`：Docker Compose 和 Nginx 配置
- `config/init.sql`：MySQL 初始化脚本

## 最小可跑通方式

下面的方式不依赖 Kafka 实时采集，适合本地演示和联调。

### 1. 启动 MySQL

如果本机没有 MySQL，推荐直接用 Docker 启动：

```powershell
cd d:\newwork\choosetreee\docker
docker compose up -d mysql
```

### 2. 启动后端

```powershell
cd d:\newwork\choosetreee
python -m venv .venv
.venv\Scripts\activate
pip install -r backend\requirements.txt
$env:MYSQL_HOST="localhost"
$env:MYSQL_PORT="3306"
$env:MYSQL_USER="root"
$env:MYSQL_PASSWORD="malware_monitor_2024"
$env:MYSQL_DATABASE="malicious_traffic"
$env:ENABLE_KAFKA="false"
python backend\app.py
```

后端启动后可访问：

- `http://localhost:5000/api/health`

### 3. 导入模拟数据

另开一个终端，执行：

```powershell
cd d:\newwork\choosetreee
.venv\Scripts\activate
$env:MYSQL_HOST="localhost"
$env:MYSQL_PORT="3306"
$env:MYSQL_USER="root"
$env:MYSQL_PASSWORD="malware_monitor_2024"
$env:MYSQL_DATABASE="malicious_traffic"
python scripts\test_insert_mock_data.py 200
```

该脚本会：

- 自动建表
- 插入 200 条模拟告警
- 生成分钟、小时、攻击类型统计

### 4. 启动前端

```powershell
cd d:\newwork\choosetreee\frontend
npm install
npm run dev
```

访问：

- `http://localhost:3000`

## Docker 全量方式

如果你希望通过 Docker 同时启动前后端、MySQL、Kafka、Nginx：

```powershell
cd d:\newwork\choosetreee\docker
docker compose up --build -d
```

访问：

- 前端：`http://localhost:8080`
- 后端健康检查：`http://localhost:5000/api/health`

说明：

- `docker-compose` 中已显式开启 `ENABLE_KAFKA=true`
- 本地直接运行后端时，默认建议设置 `ENABLE_KAFKA=false`
- 当前仓库还没有把 Suricata Producer 自动接入 Compose，因此 Docker 方式启动后不一定会自动产生实时数据

## 常见问题

### 后端能启动，但页面没有数据

先执行模拟数据导入脚本：

```powershell
python scripts\test_insert_mock_data.py 200
```

### 本地启动后端时报 Kafka 错误

请确认已经设置：

```powershell
$env:ENABLE_KAFKA="false"
```

### Docker 页面打开了，但没有实时刷新

这是当前仓库的已知限制。因为实时采集依赖 Suricata 日志和 Kafka Producer，而这部分还没有被自动编排到 `docker-compose.yml` 中。
