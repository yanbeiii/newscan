import json
import random
from datetime import datetime, timedelta

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
    ("ET SCANFTP Login Brute Force Attempt", "Attempted Information Leak", 3),
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


def generate_mock_data(count=100, output_file="mock_eve.json"):
    alerts = []
    base_time = datetime.utcnow() - timedelta(hours=24)

    for i in range(count):
        time_offset = timedelta(seconds=i * (86400 / count))
        alert = generate_alert(base_time + time_offset)
        alerts.append(json.dumps(alert))

    with open(output_file, 'w') as f:
        f.write('\n'.join(alerts))

    print(f"Generated {count} mock alerts to {output_file}")


if __name__ == '__main__':
    generate_mock_data(200)
