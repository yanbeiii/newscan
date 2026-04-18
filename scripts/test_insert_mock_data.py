from datetime import datetime, timedelta
import os
import random
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.app import create_app
from backend.models import db, Alert, MinuteStats, HourlyStats, AttackType

SIGNATURES = [
    ("ET SCAN Potential SSH Scan", "Attempted Information Leak", 2),
    ("ET WEB_SERVER SQL Injection Attempt", "Web Application Attack", 2),
    ("ET EXPLOIT Buffer Overflow", "Exploit", 1),
    ("ET MALWARE Ransomware Traffic Detected", "Malware", 1),
    ("ET DOS Potential DDoS Attack", "Denial of Service", 2),
    ("ET POLICY Suspicious HTTPS Traffic", "Policy Violation", 3),
    ("ET SCAN Nmap SYN Scan", "Attempted Information Leak", 3),
    ("ET WEB_SERVER ColdFusion Exploit", "Web Application Attack", 1),
    ("ET EXPLOIT EternalBlue SMB Exploit", "Exploit", 1),
    ("ET MALWARE Cobalt Strike Beacon", "Malware", 1),
    ("ET DOS SNMP Amplification Attack", "Denial of Service", 2),
    ("ET POLICY Suspicious DNS Query", "Policy Violation", 4),
    ("ET SCAN FTP Login Brute Force Attempt", "Attempted Information Leak", 3),
    ("ET WEB_SERVER PHPMyAdmin Access", "Web Application Attack", 3),
    ("ET EXPLOIT Java Deserialization", "Exploit", 1),
]

PROTOCOLS = ['TCP', 'UDP', 'ICMP', 'HTTP', 'HTTPS', 'DNS', 'FTP', 'SSH']
ACTIONS = ['alert', 'drop', 'pass']


def generate_ip():
    return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"


def generate_alert(base_time=None):
    if base_time is None:
        base_time = datetime.utcnow()

    signature, category, severity = random.choice(SIGNATURES)
    protocol = random.choice(PROTOCOLS)
    action = random.choice(ACTIONS)

    alert = {
        "timestamp": base_time.isoformat() + "Z",
        "event_type": "alert",
        "src_ip": generate_ip(),
        "dst_ip": generate_ip(),
        "src_port": random.randint(1024, 65535),
        "dst_port": random.choice([80, 443, 22, 21, 25, 53, 3306, 8080]),
        "proto": protocol,
        "alert": {
            "severity": severity,
            "signature": signature,
            "category": category,
            "action": action
        },
        "app_proto": protocol.lower()
    }

    return alert


def parse_severity(severity):
    if severity == 1:
        return 1
    elif severity == 2:
        return 2
    elif severity in [3, 4]:
        return 3
    else:
        return 4


def insert_mock_data(count=200):
    app = create_app()

    with app.app_context():
        db.create_all()
        print(f"Starting to insert {count} mock alerts...")

        base_time = datetime.utcnow() - timedelta(hours=24)

        for i in range(count):
            time_offset = timedelta(seconds=i * (86400 / count))
            alert_data = generate_alert(base_time + time_offset)

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
                protocol=alert_data.get('proto'),
                severity=parse_severity(alert_data.get('alert', {}).get('severity', 3)),
                signature=alert_data.get('alert', {}).get('signature'),
                category=alert_data.get('alert', {}).get('category'),
                action=alert_data.get('alert', {}).get('action'),
                raw_json=alert_data
            )

            db.session.add(alert)

            if (i + 1) % 50 == 0:
                db.session.commit()
                print(f"Inserted {i + 1} alerts...")

        db.session.commit()

        print("Updating statistics...")
        update_statistics()

        print("Mock data insertion completed!")
        print_stats()


def update_statistics():
    alerts = Alert.query.all()

    minute_stats = {}
    hourly_stats = {}
    attack_stats = {}

    for alert in alerts:
        minute = alert.timestamp.replace(second=0, microsecond=0)
        hour = alert.timestamp.replace(minute=0, second=0, microsecond=0)

        if minute not in minute_stats:
            minute_stats[minute] = {'total': 0, 'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        minute_stats[minute]['total'] += 1
        if alert.severity == 1:
            minute_stats[minute]['critical'] += 1
        elif alert.severity == 2:
            minute_stats[minute]['high'] += 1
        elif alert.severity == 3:
            minute_stats[minute]['medium'] += 1
        else:
            minute_stats[minute]['low'] += 1

        if hour not in hourly_stats:
            hourly_stats[hour] = {'total': 0, 'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        hourly_stats[hour]['total'] += 1
        if alert.severity == 1:
            hourly_stats[hour]['critical'] += 1
        elif alert.severity == 2:
            hourly_stats[hour]['high'] += 1
        elif alert.severity == 3:
            hourly_stats[hour]['medium'] += 1
        else:
            hourly_stats[hour]['low'] += 1

        attack_type = alert.category or 'Unknown'
        key = (hour, attack_type)
        if key not in attack_stats:
            attack_stats[key] = 0
        attack_stats[key] += 1

    for minute, stats in minute_stats.items():
        existing = MinuteStats.query.filter_by(minute=minute).first()
        if existing:
            existing.total_alerts = stats['total']
            existing.critical_count = stats['critical']
            existing.high_count = stats['high']
            existing.medium_count = stats['medium']
            existing.low_count = stats['low']
        else:
            ms = MinuteStats(
                minute=minute,
                total_alerts=stats['total'],
                critical_count=stats['critical'],
                high_count=stats['high'],
                medium_count=stats['medium'],
                low_count=stats['low']
            )
            db.session.add(ms)

    for hour, stats in hourly_stats.items():
        existing = HourlyStats.query.filter_by(hour=hour).first()
        if existing:
            existing.total_alerts = stats['total']
            existing.critical_count = stats['critical']
            existing.high_count = stats['high']
            existing.medium_count = stats['medium']
            existing.low_count = stats['low']
        else:
            hs = HourlyStats(
                hour=hour,
                total_alerts=stats['total'],
                critical_count=stats['critical'],
                high_count=stats['high'],
                medium_count=stats['medium'],
                low_count=stats['low']
            )
            db.session.add(hs)

    for (hour, attack_type), count in attack_stats.items():
        existing = AttackType.query.filter_by(hour=hour, attack_type=attack_type).first()
        if existing:
            existing.count = count
        else:
            at = AttackType(hour=hour, attack_type=attack_type, count=count)
            db.session.add(at)

    db.session.commit()


def print_stats():
    total = Alert.query.count()
    critical = Alert.query.filter_by(severity=1).count()
    high = Alert.query.filter_by(severity=2).count()
    medium = Alert.query.filter_by(severity=3).count()
    low = Alert.query.filter_by(severity=4).count()

    print(f"\n=== Statistics ===")
    print(f"Total Alerts: {total}")
    print(f"Critical: {critical}")
    print(f"High: {high}")
    print(f"Medium: {medium}")
    print(f"Low: {low}")


if __name__ == '__main__':
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    insert_mock_data(count)
