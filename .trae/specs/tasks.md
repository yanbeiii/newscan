# Tasks

- [ ] Task 1: 项目初始化与基础架构搭建
  - [ ] SubTask 1.1: 创建项目目录结构（backend/, frontend/, scripts/, config/, docker/）
  - [ ] SubTask 1.2: 初始化Python虚拟环境和依赖（Flask, Flask-SocketIO, kafka-python, pymysql, flask-cors, watchdog）
  - [ ] SubTask 1.3: 初始化Vue项目（Vue 3 + Vite + Element Plus + ECharts + Socket.IO Client）
  - [ ] SubTask 1.4: 编写Docker Compose配置（Zookeeper, Kafka, MySQL, Backend, Nginx）

- [ ] Task 2: 数据库设计与初始化
  - [ ] SubTask 2.1: 设计MySQL数据库表结构（alerts, minute_stats, hourly_stats, attack_types），包含字段类型、索引
  - [ ] SubTask 2.2: 编写SQL初始化脚本（建表语句 + 索引创建）
  - [ ] SubTask 2.3: 创建Flask数据库连接配置和ORM模型（使用Flask-SQLAlchemy）

- [ ] Task 3: Kafka消息队列集成
  - [ ] SubTask 3.1: 编写Kafka生产者（使用watchdog监控Suricata eve.json文件变化，按行读取新增内容并发送到Kafka）
  - [ ] SubTask 3.2: 编写Kafka消费者（接收消息并解析JSON）
  - [ ] SubTask 3.3: 使用模拟数据测试Kafka消息流转

- [ ] Task 4: 数据处理与入库
  - [ ] SubTask 4.1: 实现Suricata eve.json告警解析逻辑（提取timestamp, src_ip, dst_ip, src_port, dst_port, protocol, severity, signature, category, action, raw_json）
  - [ ] SubTask 4.2: 实现告警数据入库MySQL（写入alerts表）
  - [ ] SubTask 4.3: 实现分钟/小时统计计算与汇总表更新（minute_stats, hourly_stats, attack_types）

- [ ] Task 5: Flask后端API开发
  - [ ] SubTask 5.1: 实现告警查询API（GET /api/alerts，分页 + 多条件过滤）
  - [ ] SubTask 5.2: 实现告警详情API（GET /api/alerts/<id>）
  - [ ] SubTask 5.3: 实现仪表盘统计API（GET /api/stats/dashboard）
  - [ ] SubTask 5.4: 实现趋势分析API（GET /api/stats/trend，支持分钟/小时/天粒度）
  - [ ] SubTask 5.5: 实现攻击类型分布API（GET /api/stats/attack-types）
  - [ ] SubTask 5.6: 实现IP排行API（GET /api/stats/top-ips）
  - [ ] SubTask 5.7: 配置CORS

- [ ] Task 6: WebSocket实时推送开发
  - [ ] SubTask 6.1: 集成Flask-SocketIO，配置WebSocket服务
  - [ ] SubTask 6.2: 在数据处理入库完成后，通过SocketIO推送new_alert事件（告警摘要）
  - [ ] SubTask 6.3: 在数据处理入库完成后，通过SocketIO推送stats_update事件（统计更新）
  - [ ] SubTask 6.4: 前端集成Socket.IO Client，连接WebSocket服务
  - [ ] SubTask 6.5: 前端监听new_alert事件，自动更新最新告警列表
  - [ ] SubTask 6.6: 前端监听stats_update事件，自动更新仪表盘统计卡片

- [ ] Task 7: Vue前端界面开发
  - [ ] SubTask 7.1: 创建主页面布局（Element Plus侧边栏导航）和路由配置（仪表盘、告警列表、统计分析）
  - [ ] SubTask 7.2: 开发仪表盘页面（统计卡片 + 告警趋势折线图 + 攻击类型饼图 + 最新告警列表）
  - [ ] SubTask 7.3: 开发告警列表页面（Element Plus表格 + 分页 + 时间/IP/级别/协议过滤 + 详情对话框）
  - [ ] SubTask 7.4: 开发统计分析页面（攻击类型分布图 + 时间趋势图 + IP排行表格）

- [ ] Task 8: 系统集成与测试
  - [ ] SubTask 8.1: 编写模拟数据生成脚本（生成Suricata eve.json格式的测试告警数据）
  - [ ] SubTask 8.2: Docker Compose一键启动全部服务，验证各服务正常连接
  - [ ] SubTask 8.3: 端到端数据流测试（模拟数据 → Kafka → 处理 → 数据库 → API → WebSocket → 前端）
  - [ ] SubTask 8.4: 前端API联调测试（各页面功能验证）

# Task Dependencies
- [Task 2] depends on [Task 1] (数据库初始化需要项目基础结构)
- [Task 3] depends on [Task 1] (Kafka集成需要Docker环境)
- [Task 4] depends on [Task 2, Task 3] (数据处理需要数据库和Kafka就绪)
- [Task 5] depends on [Task 4] (API开发需要数据入库逻辑完成)
- [Task 6] depends on [Task 4, Task 5] (WebSocket需要数据处理和API基础)
- [Task 7] depends on [Task 5, Task 6] (前端开发需要后端API和WebSocket完成)
- [Task 8] depends on [Task 7] (系统测试需要全部功能完成)

# 并行执行建议
- Task 1 的子任务可以并行执行
- Task 2 和 Task 3 可以并行执行（数据库和Kafka是独立的）
- Task 5 和 Task 6 可以部分并行（WebSocket集成可与API开发同步进行）
- Task 7 的 SubTask 7.1 可以与 Task 5/6 并行（前端布局不依赖具体API实现）
