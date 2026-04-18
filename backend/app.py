from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from backend.models import db, Alert, MinuteStats, HourlyStats, AttackType
from backend.config import Config

app = Flask(__name__)
app.config.from_object(Config)
CORS(app, resources={r"/api/*": {"origins": Config.CORS_ORIGINS}})
db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')


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
        query = query.filter(Alert.timestamp >= datetime.fromisoformat(start_time))
    if end_time:
        query = query.filter(Alert.timestamp <= datetime.fromisoformat(end_time))
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
        start = datetime.fromisoformat(start_time)
    else:
        start = datetime.utcnow() - timedelta(days=7)

    if end_time:
        end = datetime.fromisoformat(end_time)
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
        start = datetime.fromisoformat(start_time)
    else:
        start = datetime.utcnow() - timedelta(days=7)

    if end_time:
        end = datetime.fromisoformat(end_time)
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
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)
