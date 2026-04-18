# Checklist

## 基础设施
- [ ] 项目目录结构正确创建（backend/, frontend/, scripts/, config/, docker/）
- [ ] Python依赖正确安装（Flask, Flask-SocketIO, kafka-python, pymysql, flask-cors, watchdog等）
- [ ] Vue项目正确初始化并安装依赖（Element Plus, ECharts, Socket.IO Client, axios）
- [ ] Docker Compose配置包含全部服务（Zookeeper, Kafka, MySQL, Backend, Nginx）
- [ ] Docker内部网络配置正确，各服务可通过服务名互相访问
- [ ] Nginx正确配置前端静态资源服务和API反向代理

## 数据库
- [ ] MySQL数据库表正确创建（alerts, minute_stats, hourly_stats, attack_types）
- [ ] 数据库字段类型和长度合理设计
- [ ] 索引正确创建（timestamp, severity, src_ip, minute, hour, hour+attack_type联合索引）
- [ ] alerts表包含完整字段（timestamp, src_ip, dst_ip, src_port, dst_port, protocol, severity, signature, category, action, raw_json, created_at）
- [ ] minute_stats表支持分钟级统计（total_alerts, critical_count, high_count, medium_count, low_count）
- [ ] Flask-SQLAlchemy ORM模型正确定义

## Kafka消息队列
- [ ] Kafka生产者能够使用watchdog监控Suricata eve.json文件变化
- [ ] Kafka生产者能够正确按行读取新增日志内容
- [ ] Kafka生产者能够正确将告警数据发送到malicious_traffic主题
- [ ] Kafka消费者能够正确接收消息并解析JSON
- [ ] Kafka消息流转测试通过（使用模拟数据）

## 数据处理与入库
- [ ] Suricata eve.json告警JSON格式正确解析（时间、源IP、目的IP、端口、协议、告警级别、签名、分类、动作等）
- [ ] 解析后的数据正确写入alerts表（包含raw_json原始数据）
- [ ] 分钟统计数据正确计算并写入minute_stats表
- [ ] 小时统计数据正确计算并写入hourly_stats表
- [ ] 攻击类型统计数据正确计算并写入attack_types表

## Flask后端API
- [ ] GET /api/alerts 接口返回分页告警列表，支持多条件过滤（时间范围、源IP、目的IP、告警级别、协议）
- [ ] GET /api/alerts/<id> 接口返回单条告警详情
- [ ] GET /api/stats/dashboard 接口返回仪表盘统计数据（总告警数、各等级数量、最近24小时趋势、最新N条）
- [ ] GET /api/stats/trend 接口返回告警趋势数据，支持分钟/小时/天粒度
- [ ] GET /api/stats/attack-types 接口返回攻击类型分布
- [ ] GET /api/stats/top-ips 接口返回IP排行
- [ ] CORS配置正确，前端可正常调用API

## WebSocket实时推送
- [ ] Flask-SocketIO正确集成和配置
- [ ] 后端在数据处理入库完成后推送new_alert事件（告警摘要）
- [ ] 后端在数据处理入库完成后推送stats_update事件（统计更新）
- [ ] 前端Socket.IO Client正确连接WebSocket服务
- [ ] 前端监听new_alert事件，自动更新最新告警列表
- [ ] 前端监听stats_update事件，自动更新仪表盘统计卡片

## 前端界面
- [ ] 前端主页面布局正确（Element Plus侧边栏导航）
- [ ] 前端路由配置正确（仪表盘、告警列表、统计分析）
- [ ] 仪表盘页面显示统计卡片（总告警数、各等级数量）
- [ ] 仪表盘页面显示告警趋势折线图（ECharts）
- [ ] 仪表盘页面显示攻击类型分布饼图（ECharts）
- [ ] 仪表盘页面显示最新告警列表
- [ ] 仪表盘页面通过WebSocket自动刷新数据
- [ ] 告警列表页面支持分页显示
- [ ] 告警列表页面支持按条件过滤（时间范围、IP、告警级别、协议）
- [ ] 点击告警可查看详情对话框（包含完整告警信息）
- [ ] 统计分析页面展示攻击类型分布图表
- [ ] 统计分析页面展示时间趋势图表
- [ ] 统计分析页面展示IP排行表格

## 系统集成与测试
- [ ] 模拟数据生成脚本可正确生成Suricata eve.json格式的测试数据
- [ ] Docker Compose一键启动全部服务成功
- [ ] 各服务之间网络连接正常（Backend → MySQL, Backend → Kafka, Frontend → Backend API）
- [ ] 端到端数据流测试通过（模拟数据 → Kafka → 处理 → 数据库 → API → WebSocket → 前端）
- [ ] 前端各页面功能验证通过
