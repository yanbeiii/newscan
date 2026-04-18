CREATE DATABASE IF NOT EXISTS malicious_traffic;
USE malicious_traffic;

CREATE TABLE IF NOT EXISTS alerts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    src_ip VARCHAR(45),
    dst_ip VARCHAR(45),
    src_port INT,
    dst_port INT,
    protocol VARCHAR(20),
    severity SMALLINT,
    signature VARCHAR(255),
    category VARCHAR(100),
    action VARCHAR(20),
    raw_json JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timestamp (timestamp),
    INDEX idx_severity (severity),
    INDEX idx_src_ip (src_ip)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS minute_stats (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    minute DATETIME NOT NULL,
    total_alerts INT DEFAULT 0,
    critical_count INT DEFAULT 0,
    high_count INT DEFAULT 0,
    medium_count INT DEFAULT 0,
    low_count INT DEFAULT 0,
    INDEX idx_minute (minute)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS hourly_stats (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    hour DATETIME NOT NULL,
    total_alerts INT DEFAULT 0,
    critical_count INT DEFAULT 0,
    high_count INT DEFAULT 0,
    medium_count INT DEFAULT 0,
    low_count INT DEFAULT 0,
    INDEX idx_hour (hour)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS attack_types (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    hour DATETIME NOT NULL,
    attack_type VARCHAR(100),
    count INT DEFAULT 0,
    INDEX idx_hour (hour),
    INDEX idx_hour_type (hour, attack_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
