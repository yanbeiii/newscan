import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'malicious-traffic-monitor-secret-key-2024')

    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'mysql')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'malware_monitor_2024')
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'malicious_traffic')

    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }

    KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
    KAFKA_TOPIC = 'malicious_traffic'

    SURICATA_LOG_PATH = os.environ.get('SURICATA_LOG_PATH', '/var/log/suricata/eve.json')

    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*')
