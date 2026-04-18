from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from backend.models import db, Alert, MinuteStats, HourlyStats, AttackType
from backend.config import Config
import json
import logging
import threading
from kafka import KafkaConsumer
from kafka.errors import KafkaError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

socketio = SocketIO(cors_allowed_origins="*", async_mode='gevent')


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})
    db.init_app(app)
    socketio.init_app(app)
    return app


app = create_app()


def parse_iso_datetime(time_str):
    if not time_str:
        return None
    if time_str.endswith('Z'):
        time_str = time_str[:-1] + '+00:00'
    try:
        return datetime.fromisoformat(time_str)
    except (ValueError, TypeError):
        return None


def parse_severity(severity):
    severity = int(severity) if severity else 3
    if severity == 1:
        return 1
    elif severity == 2:
        return 2
    elif severity in [3, 4]:
        return 3
    else:
        return 4


def update_stats(alert_data):
    try:
        timestamp = parse_iso_datetime(alert_data.get('timestamp'))
        if not timestamp:
            timestamp = datetime.utcnow()
    except:
        timestamp = datetime.utcnow()

    minute = timestamp.replace(second=0, microsecond=0)
    hour = timestamp.replace(minute=0, second=0, microsecond=0)

    severity = parse_severity(alert_data.get('severity'))

    minute_stat = MinuteStats.query.filter_by(minute=minute).first()
    if not minute_stat:
        minute_stat = MinuteStats(
            minute=minute,
            total_alerts=0,
            critical_count=0,
            high_count=0,
            medium_count=0,
            low_count=0
        )
        db.session.add(minute_stat)

    minute_stat.total_alerts += 1
    if severity == 1:
        minute_stat.critical_count += 1
    elif severity == 2:
        minute_stat.high_count += 1
    elif severity == 3:
        minute_stat.medium_count += 1
    else:
        minute_stat.low_count += 1

    hourly_stat = HourlyStats.query.filter_by(hour=hour).first()
    if not hourly_stat:
        hourly_stat = HourlyStats(
            hour=hour,
            total_alerts=0,
            critical_count=0,
            high_count=0,
            medium_count=0,
            low_count=0
        )
        db.session.add(hourly_stat)

    hourly_stat.total_alerts += 1
    if severity == 1:
        hourly_stat.critical_count += 1
    elif severity == 2:
        hourly_stat.high_count += 1
    elif severity == 3:
        hourly_stat.medium_count += 1
    else:
        hourly_stat.low_count += 1

    attack_type = alert_data.get('category', 'Unknown')
    attack_stat = AttackType.query.filter_by(hour=hour, attack_type=attack_type).first()
    if not attack_stat:
        attack_stat = AttackType(hour=hour, attack_type=attack_type, count=0)
        db.session.add(attack_stat)

    attack_stat.count += 1
    db.session.commit()


def process_alert(alert_data):
    timestamp = parse_iso_datetime(alert_data.get('timestamp'))
    if not timestamp:
        timestamp = datetime.utcnow()

    severity = parse_severity(alert_data.get('severity'))

    alert = Alert(
        timestamp=timestamp,
        src_ip=alert_data.get('src_ip'),
        dst_ip=alert_data.get('dst_ip'),
        src_port=alert_data.get('src_port'),
        dst_port=alert_data.get('dst_port'),
        protocol=alert_data.get('protocol'),
        severity=severity,
        signature=alert_data.get('signature'),
        category=alert_data.get('category'),
        action=alert_data.get('action'),
        raw_json=alert_data.get('raw_json')
    )

    db.session.add(alert)
    db.session.commit()

    update_stats(alert_data)

    alert_summary = {
        'id': alert.id,
        'timestamp': alert.timestamp.isoformat(),
        'src_ip': alert.src_ip,
        'dst_ip': alert.dst_ip,
        'protocol': alert.protocol,
        'severity': alert.severity,
        'signature': alert.signature,
        'category': alert.category
    }
    socketio.emit('new_alert', alert_summary)

    total = Alert.query.count()
    critical = Alert.query.filter_by(severity=1).count()
    high = Alert.query.filter_by(severity=2).count()
    medium = Alert.query.filter_by(severity=3).count()
    low = Alert.query.filter_by(severity=4).count()

    stats_update = {
        'total_alerts': total,
        'critical_count': critical,
        'high_count': high,
        'medium_count': medium,
        'low_count': low
    }
    socketio.emit('stats_update', stats_update)

    logger.info(f"Processed alert: {alert.signature}")
    return alert_summary


def start_kafka_consumer(app):
    bootstrap_servers = app.config.get('KAFKA_BOOTSTRAP_SERVERS') or 'kafka:9092'
    topic = app.config.get('KAFKA_TOPIC', 'malicious_traffic')
    group_id = 'malicious_traffic_consumer_group'

    try:
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=True
        )
        logger.info("Kafka consumer started")

        def consume_messages():
            for message in consumer:
                try:
                    alert_data = message.value
                    with app.app_context():
                        process_alert(alert_data)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")

        consumer_thread = threading.Thread(target=consume_messages, daemon=True)
        consumer_thread.start()
    except KafkaError as e:
        logger.error(f"Kafka consumer error: {e}")
    except Exception as e:
        logger.error(f"Failed to start Kafka consumer: {e}")


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'malicious-traffic-monitor'})


@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    src_ip = request.args.get('src_ip')
    dst_ip = request.args.get('dst_ip')
    severity = request.args.get('severity', type=int)
    protocol = request.args.get('protocol')

    query = Alert.query

    if start_time:
        parsed_start = parse_iso_datetime(start_time)
        if parsed_start is None:
            return jsonify({'error': 'Invalid start_time format'}), 400
        query = query.filter(Alert.timestamp >= parsed_start)
    if end_time:
        parsed_end = parse_iso_datetime(end_time)
        if parsed_end is None:
            return jsonify({'error': 'Invalid end_time format'}), 400
        query = query.filter(Alert.timestamp <= parsed_end)
    if src_ip:
        query = query.filter(Alert.src_ip == src_ip)
    if dst_ip:
        query = query.filter(Alert.dst_ip == dst_ip)
    if severity:
        query = query.filter(Alert.severity == severity)
    if protocol:
        query = query.filter(Alert.protocol == protocol)

    query = query.order_by(Alert.timestamp.desc())

    total = query.count()
    alerts = query.offset((page - 1) * page_size).limit(page_size).all()

    return jsonify({
        'total': total,
        'page': page,
        'page_size': page_size,
        'data': [alert.to_dict() for alert in alerts]
    })


@app.route('/api/alerts/<int:alert_id>', methods=['GET'])
def get_alert(alert_id):
    alert = Alert.query.get(alert_id)
    if not alert:
        return jsonify({'error': 'Alert not found'}), 404
    return jsonify(alert.to_dict())


@app.route('/api/stats/dashboard', methods=['GET'])
def get_dashboard_stats():
    total = Alert.query.count()
    critical = Alert.query.filter_by(severity=1).count()
    high = Alert.query.filter_by(severity=2).count()
    medium = Alert.query.filter_by(severity=3).count()
    low = Alert.query.filter_by(severity=4).count()

    recent_time = datetime.utcnow() - timedelta(hours=24)
    recent_alerts = Alert.query.filter(Alert.timestamp >= recent_time).order_by(Alert.timestamp.desc()).limit(10).all()

    last_24_hours = []
    for i in range(24):
        hour_time = datetime.utcnow().replace(minute=0, second=0, microsecond=0) - timedelta(hours=23-i)
        next_hour = hour_time + timedelta(hours=1)
        hour_stat = HourlyStats.query.filter(
            and_(HourlyStats.hour >= hour_time, HourlyStats.hour < next_hour)
        ).first()
        last_24_hours.append({
            'hour': hour_time.isoformat(),
            'total_alerts': hour_stat.total_alerts if hour_stat else 0
        })

    return jsonify({
        'total_alerts': total,
        'critical_count': critical,
        'high_count': high,
        'medium_count': medium,
        'low_count': low,
        'recent_alerts': [alert.to_dict() for alert in recent_alerts],
        'last_24_hours': last_24_hours
    })


@app.route('/api/stats/trend', methods=['GET'])
def get_trend():
    granularity = request.args.get('granularity', 'hour')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')

    if start_time:
        start = parse_iso_datetime(start_time)
        if start is None:
            return jsonify({'error': 'Invalid start_time format'}), 400
    else:
        start = datetime.utcnow() - timedelta(days=7)

    if end_time:
        end = parse_iso_datetime(end_time)
        if end is None:
            return jsonify({'error': 'Invalid end_time format'}), 400
    else:
        end = datetime.utcnow()

    if granularity == 'minute':
        stats = MinuteStats.query.filter(
            and_(MinuteStats.minute >= start, MinuteStats.minute <= end)
        ).order_by(MinuteStats.minute).all()
        data = [{'time': s.minute.isoformat(), 'total_alerts': s.total_alerts,
                 'critical': s.critical_count, 'high': s.high_count,
                 'medium': s.medium_count, 'low': s.low_count} for s in stats]
    elif granularity == 'day':
        stats = db.session.query(
            func.date(HourlyStats.hour).label('date'),
            func.sum(HourlyStats.total_alerts).label('total'),
            func.sum(HourlyStats.critical_count).label('critical'),
            func.sum(HourlyStats.high_count).label('high'),
            func.sum(HourlyStats.medium_count).label('medium'),
            func.sum(HourlyStats.low_count).label('low')
        ).filter(
            and_(HourlyStats.hour >= start, HourlyStats.hour <= end)
        ).group_by(func.date(HourlyStats.hour)).order_by(func.date(HourlyStats.hour)).all()
        data = [{'time': str(s.date), 'total_alerts': s.total,
                 'critical': s.critical, 'high': s.high,
                 'medium': s.medium, 'low': s.low} for s in stats]
    else:
        stats = HourlyStats.query.filter(
            and_(HourlyStats.hour >= start, HourlyStats.hour <= end)
        ).order_by(HourlyStats.hour).all()
        data = [{'time': s.hour.isoformat(), 'total_alerts': s.total_alerts,
                 'critical': s.critical_count, 'high': s.high_count,
                 'medium': s.medium_count, 'low': s.low_count} for s in stats]

    return jsonify({'granularity': granularity, 'data': data})


@app.route('/api/stats/attack-types', methods=['GET'])
def get_attack_types():
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')

    if start_time:
        start = parse_iso_datetime(start_time)
        if start is None:
            return jsonify({'error': 'Invalid start_time format'}), 400
    else:
        start = datetime.utcnow() - timedelta(days=7)

    if end_time:
        end = parse_iso_datetime(end_time)
        if end is None:
            return jsonify({'error': 'Invalid end_time format'}), 400
    else:
        end = datetime.utcnow()

    stats = db.session.query(
        AttackType.attack_type,
        func.sum(AttackType.count).label('total')
    ).filter(
        and_(AttackType.hour >= start, AttackType.hour <= end)
    ).group_by(AttackType.attack_type).order_by(func.sum(AttackType.count).desc()).all()

    data = [{'attack_type': s.attack_type, 'count': s.total} for s in stats]
    return jsonify({'data': data})


@app.route('/api/stats/top-ips', methods=['GET'])
def get_top_ips():
    ip_type = request.args.get('type', 'src')
    limit = request.args.get('limit', 10, type=int)

    if ip_type == 'src':
        stats = db.session.query(
            Alert.src_ip,
            func.count(Alert.id).label('count')
        ).filter(Alert.src_ip.isnot(None)).group_by(
            Alert.src_ip
        ).order_by(func.count(Alert.id).desc()).limit(limit).all()
    else:
        stats = db.session.query(
            Alert.dst_ip,
            func.count(Alert.id).label('count')
        ).filter(Alert.dst_ip.isnot(None)).group_by(
            Alert.dst_ip
        ).order_by(func.count(Alert.id).desc()).limit(limit).all()

    data = [{'ip': s[0], 'count': s[1]} for s in stats]
    return jsonify({'type': ip_type, 'data': data})


@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connected', {'status': 'connected'})


@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


@socketio.on('request_stats')
def handle_request_stats():
    total = Alert.query.count()
    critical = Alert.query.filter_by(severity=1).count()
    high = Alert.query.filter_by(severity=2).count()
    medium = Alert.query.filter_by(severity=3).count()
    low = Alert.query.filter_by(severity=4).count()

    stats_update = {
        'total_alerts': total,
        'critical_count': critical,
        'high_count': high,
        'medium_count': medium,
        'low_count': low
    }
    emit('stats_update', stats_update)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    if app.config.get('ENABLE_KAFKA'):
        start_kafka_consumer(app)
    else:
        logger.info("Kafka consumer disabled; running in API-only mode")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)
