import json
import logging
from datetime import datetime
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from backend.models import db, Alert, MinuteStats, HourlyStats, AttackType
from flask import Flask
from flask_socketio import SocketIO
from backend.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app


socketio = SocketIO()


def parse_severity(severity):
    if severity == 1:
        return 1
    elif severity == 2:
        return 2
    elif severity in [3, 4]:
        return 3
    else:
        return 4


def update_stats(app, alert_data):
    with app.app_context():
        try:
            timestamp = datetime.fromisoformat(alert_data['timestamp'].replace('Z', '+00:00'))
        except:
            timestamp = datetime.utcnow()

        minute = timestamp.replace(second=0, microsecond=0)
        hour = timestamp.replace(minute=0, second=0, microsecond=0)

        severity = parse_severity(alert_data.get('severity', 3))

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


def process_alert(app, alert_data):
    with app.app_context():
        try:
            timestamp = datetime.fromisoformat(alert_data['timestamp'].replace('Z', '+00:00'))
        except:
            timestamp = datetime.utcnow()

        alert = Alert(
            timestamp=timestamp,
            src_ip=alert_data.get('src_ip'),
            dst_ip=alert_data.get('dst_ip'),
            src_port=alert_data.get('src_port'),
            dst_port=alert_data.get('dst_port'),
            protocol=alert_data.get('protocol'),
            severity=parse_severity(alert_data.get('severity', 3)),
            signature=alert_data.get('signature'),
            category=alert_data.get('category'),
            action=alert_data.get('action'),
            raw_json=alert_data.get('raw_json')
        )

        db.session.add(alert)
        db.session.commit()

        update_stats(app, alert_data)

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


def main():
    app = create_app()
    socketio.init_app(app, cors_allowed_origins="*", async_mode='gevent')

    bootstrap_servers = 'kafka:9092'
    topic = 'malicious_traffic'
    group_id = 'malicious_traffic_consumer_group'

    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        group_id=group_id,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        enable_auto_commit=True
    )

    logger.info("Kafka consumer started with SocketIO support")

    def consume_messages():
        for message in consumer:
            try:
                alert_data = message.value
                process_alert(app, alert_data)
            except Exception as e:
                logger.error(f"Error processing message: {e}")

    import gevent
    gevent.spawn(consume_messages)

    socketio.run(app, host='0.0.0.0', port=5001, debug=False)


if __name__ == '__main__':
    main()
