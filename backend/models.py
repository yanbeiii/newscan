from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Alert(db.Model):
    __tablename__ = 'alerts'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    timestamp = db.Column(db.DateTime, index=True, nullable=False)
    src_ip = db.Column(db.String(45), index=True)
    dst_ip = db.Column(db.String(45))
    src_port = db.Column(db.Integer)
    dst_port = db.Column(db.Integer)
    protocol = db.Column(db.String(20))
    severity = db.Column(db.SmallInteger, index=True)
    signature = db.Column(db.String(255))
    category = db.Column(db.String(100))
    action = db.Column(db.String(20))
    raw_json = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'src_ip': self.src_ip,
            'dst_ip': self.dst_ip,
            'src_port': self.src_port,
            'dst_port': self.dst_port,
            'protocol': self.protocol,
            'severity': self.severity,
            'signature': self.signature,
            'category': self.category,
            'action': self.action,
            'raw_json': self.raw_json,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class MinuteStats(db.Model):
    __tablename__ = 'minute_stats'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    minute = db.Column(db.DateTime, index=True, nullable=False)
    total_alerts = db.Column(db.Integer, default=0)
    critical_count = db.Column(db.Integer, default=0)
    high_count = db.Column(db.Integer, default=0)
    medium_count = db.Column(db.Integer, default=0)
    low_count = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'minute': self.minute.isoformat() if self.minute else None,
            'total_alerts': self.total_alerts,
            'critical_count': self.critical_count,
            'high_count': self.high_count,
            'medium_count': self.medium_count,
            'low_count': self.low_count
        }


class HourlyStats(db.Model):
    __tablename__ = 'hourly_stats'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    hour = db.Column(db.DateTime, index=True, nullable=False)
    total_alerts = db.Column(db.Integer, default=0)
    critical_count = db.Column(db.Integer, default=0)
    high_count = db.Column(db.Integer, default=0)
    medium_count = db.Column(db.Integer, default=0)
    low_count = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'hour': self.hour.isoformat() if self.hour else None,
            'total_alerts': self.total_alerts,
            'critical_count': self.critical_count,
            'high_count': self.high_count,
            'medium_count': self.medium_count,
            'low_count': self.low_count
        }


class AttackType(db.Model):
    __tablename__ = 'attack_types'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    hour = db.Column(db.DateTime, index=True, nullable=False)
    attack_type = db.Column(db.String(100))
    count = db.Column(db.Integer, default=0)

    __table_args__ = (
        db.Index('idx_hour_type', 'hour', 'attack_type'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'hour': self.hour.isoformat() if self.hour else None,
            'attack_type': self.attack_type,
            'count': self.count
        }
