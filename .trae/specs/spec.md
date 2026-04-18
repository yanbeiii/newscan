# 恶意流量实时监控与可视化平台 Spec

## Why
网络安全威胁日益增加，传统流量分析工具缺乏实时监控和可视化能力。本项目旨在设计并实现一个恶意流量监控系统，通过Suricata进行流量检测，Kafka进行消息传递，Flask后端处理，Vue前端展示，为网络安全分析人员提供直观的实时监控能力。

## What Changes
- 新建完整的五层架构系统（数据采集层、消息队列层、分析处理层、存储层、可视化展示层）
- 实现Suricata告警日志的实时采集与解析
- 实现Kafka消息队列的集成与消息流转
- 实现Flask RESTful API后端服务
- 实现WebSocket实时推送能力
- 实现Vue前端可视化界面
- 实现MySQL数据库的流量数据存储

## Impact
- 影响系统：全新的监控系统
- 技术栈：Suricata 7.x + Kafka 3.x + Python 3.10+ + Flask 3.x + Flask-SocketIO + Vue 3 + MySQL 8.x
- 架构：五层分布式架构
- 部署方式：Docker Compose 一键部署

## ADDED Requirements

### Requirement: 数据采集层
系统 SHALL 通过Suricata实时监控网络流量，生成JSON格式的告警日志（eve.json）。

#### Scenario: Suricata启动流量监控
- **WHEN** Suricata启动并配置为输出JSON告警日志
- **THEN** 系统能够在指定目录实时生成eve.json日志文件

### Requirement: 消息队列层
系统 SHALL 使用Kafka作为消息中间件，实现日志采集端与分析处理端之间的解耦。

#### Scenario: Kafka消息发布与订阅
- **WHEN** 日志采集器读取到新的Suricata告警日志
- **THEN** 告警数据被发布到Kafka的malicious_traffic主题
- **AND** 分析处理服务能够消费该主题的消息

### Requirement: 分析处理层
系统 SHALL 使用Python消费Kafka消息，进行数据解析、分类和统计，并写入MySQL数据库。

#### Scenario: 恶意告警数据处理
- **WHEN** Python消费者从Kafka获取到Suricata告警消息
- **THEN** 解析告警字段（时间、源IP、目的IP、源端口、目的端口、协议、告警级别、攻击类型、动作等）
- **AND** 将解析后的数据写入MySQL数据库
- **AND** 通过WebSocket将新告警实时推送给前端

### Requirement: 存储层
系统 SHALL 使用MySQL数据库存储告警数据、统计数据。

#### Scenario: 数据库表设计
- **WHEN** 系统启动时
- **THEN** 自动创建或确认告警记录表(alerts)、分钟统计表(minute_stats)、小时统计表(hourly_stats)、攻击类型统计表(attack_types)存在

### Requirement: 可视化展示层
系统 SHALL 使用Vue + Element Plus构建前端界面，通过Flask API获取数据并展示，通过WebSocket接收实时告警推送。

#### Scenario: 实时告警展示
- **WHEN** 用户访问监控仪表盘页面
- **THEN** 显示实时告警数量、攻击类型分布饼图、告警趋势折线图、最新告警列表
- **AND** 新告警到达时通过WebSocket自动更新页面数据，无需手动刷新

#### Scenario: 告警详情查询
- **WHEN** 用户点击某条告警记录
- **THEN** 显示该告警的详细信息（源IP、目的IP、端口、协议、告警级别、攻击特征、动作等）

#### Scenario: WebSocket实时推送
- **WHEN** 后端处理完一条新告警并写入数据库后
- **THEN** 通过Flask-SocketIO将告警摘要推送给所有已连接的前端客户端
- **AND** 前端收到推送后自动更新仪表盘统计数据和最新告警列表

## 系统架构设计

### 数据采集层
- **组件**: Suricata IDS
- **功能**: 网络流量抓包、规则匹配、告警生成
- **输出**: JSON格式告警日志文件（eve.json）
- **日志格式**: Suricata eve.json 标准格式，每行一条JSON记录

### 消息队列层
- **组件**: Apache Kafka
- **主题**: malicious_traffic（单主题，1个分区）
- **生产者**: Python日志采集脚本（使用watchdog/inotify监控Suricata日志文件变化，按行读取新增内容）
- **消费者**: Python数据处理服务

### 分析处理层
- **组件**: Python 3.10+ (kafka-python)
- **功能**:
  - 消息解析与字段提取
  - 告警级别分类（紧急/高/中/低/信息）
  - 实时统计计算（每分钟/每小时告警数、攻击TOP N）
  - 数据清洗与入库
  - WebSocket实时推送新告警

### 存储层
- **组件**: MySQL 8.x
- **核心表**:
  - `alerts`: 告警记录表
    - id (BIGINT, 自增主键)
    - timestamp (DATETIME, 索引, 告警发生时间)
    - src_ip (VARCHAR(45), 源IP)
    - dst_ip (VARCHAR(45), 目的IP)
    - src_port (INT, 源端口)
    - dst_port (INT, 目的端口)
    - protocol (VARCHAR(20), 协议类型: TCP/UDP/ICMP等)
    - severity (TINYINT, 告警级别: 1-4)
    - signature (VARCHAR(255), 告警签名/规则描述)
    - category (VARCHAR(100), 攻击分类)
    - action (VARCHAR(20), 动作: alert/drop/pass)
    - raw_json (JSON, 原始告警JSON，便于后续扩展)
    - created_at (DATETIME, 记录创建时间)
    - **索引**: idx_timestamp (timestamp), idx_severity (severity), idx_src_ip (src_ip)
  - `minute_stats`: 分钟统计表（支持实时看板）
    - id (BIGINT, 自增主键)
    - minute (DATETIME, 索引, 统计时间精确到分钟)
    - total_alerts (INT, 总告警数)
    - critical_count (INT, 紧急告警数, severity=1)
    - high_count (INT, 高级告警数, severity=2)
    - medium_count (INT, 中级告警数, severity=3)
    - low_count (INT, 低级告警数, severity=4)
    - **索引**: idx_minute (minute)
  - `hourly_stats`: 小时统计表（用于趋势分析）
    - id (BIGINT, 自增主键)
    - hour (DATETIME, 索引, 统计时间精确到小时)
    - total_alerts (INT, 总告警数)
    - critical_count (INT, 紧急告警数)
    - high_count (INT, 高级告警数)
    - medium_count (INT, 中级告警数)
    - low_count (INT, 低级告警数)
    - **索引**: idx_hour (hour)
  - `attack_types`: 攻击类型统计表
    - id (BIGINT, 自增主键)
    - hour (DATETIME, 索引, 统计时间精确到小时)
    - attack_type (VARCHAR(100), 攻击类型)
    - count (INT, 该类型告警数量)
    - **索引**: idx_hour_type (hour, attack_type)

### 可视化展示层
- **前端**: Vue 3 + Element Plus + ECharts + Socket.IO Client
- **后端API**: Flask 3.x RESTful API + Flask-SocketIO
- **核心页面**:
  - 仪表盘（Dashboard）：总览统计、实时图表、WebSocket自动刷新
  - 告警列表：分页查询、条件过滤、详情查看
  - 统计分析：攻击类型分布、时间趋势、IP排行

## API接口设计

### RESTful API

#### GET /api/alerts
获取告警列表，支持分页和条件查询
- 参数: page, page_size, start_time, end_time, src_ip, dst_ip, severity, protocol

#### GET /api/alerts/<id>
获取单条告警详情

#### GET /api/stats/dashboard
获取仪表盘统计数据（总告警数、各等级数量、最近24小时趋势、最新N条记录）

#### GET /api/stats/trend
获取告警趋势数据（按时间聚合，支持分钟/小时/天粒度）
- 参数: granularity (minute/hour/day), start_time, end_time

#### GET /api/stats/attack-types
获取攻击类型分布数据
- 参数: start_time, end_time

#### GET /api/stats/top-ips
获取告警最多的源IP/目的IP排行
- 参数: type (src/dst), limit

### WebSocket 事件

#### 事件: new_alert
后端向前端推送新告警摘要
- 数据: { id, timestamp, src_ip, dst_ip, protocol, severity, signature, category }

#### 事件: stats_update
后端向前端推送统计更新
- 数据: { total_alerts, critical_count, high_count, medium_count, low_count }

## 部署架构

### Docker Compose 服务清单
| 服务 | 说明 |
|------|------|
| zookeeper | Kafka 依赖的协调服务 |
| kafka | 消息队列 |
| mysql | 数据库 |
| backend | Flask 后端 (Flask + Flask-SocketIO) |
| nginx | 前端静态资源服务 + API 反向代理 |

### 网络配置
- 所有服务通过 Docker 内部网络通信
- 仅暴露前端端口（80）和 Suricata 端口（如需外部访问）
