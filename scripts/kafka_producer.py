import json
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from kafka import KafkaProducer
from kafka.errors import KafkaError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EveJsonHandler(FileSystemEventHandler):
    def __init__(self, file_path, producer, topic):
        self.file_path = file_path
        self.producer = producer
        self.topic = topic
        self.file_handle = None
        self.position = 0

    def on_modified(self, event):
        if event.src_path == self.file_path:
            self.read_new_lines()

    def on_created(self, event):
        if event.src_path == self.file_path:
            self.open_file()

    def read_new_lines(self):
        try:
            if self.file_handle is None:
                self.open_file()

            if self.file_handle:
                self.file_handle.seek(self.position)
                lines = self.file_handle.readlines()
                for line in lines:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            if data.get('event_type') == 'alert':
                                alert_data = self.extract_alert_data(data)
                                self.send_to_kafka(alert_data)
                        except json.JSONDecodeError:
                            pass
                self.position = self.file_handle.tell()
        except Exception as e:
            logger.error(f"Error reading new lines: {e}")

    def open_file(self):
        try:
            self.file_handle = open(self.file_path, 'r', encoding='utf-8')
            self.file_handle.seek(0, 2)
            self.position = self.file_handle.tell()
            logger.info(f"Opened file {self.file_path}")
        except Exception as e:
            logger.error(f"Error opening file: {e}")

    def extract_alert_data(self, data):
        alert = data.get('alert', {})
        src_ip = None
        src_port = None
        dst_ip = None
        dst_port = None
        protocol = None

        if 'src_ip' in data:
            src_ip = data['src_ip']
        if 'src_port' in data:
            src_port = data['src_port']
        if 'dst_ip' in data:
            dst_ip = data['dst_ip']
        if 'dst_port' in data:
            dst_port = data['dst_port']
        if 'proto' in data:
            protocol = data['proto']

        return {
            'timestamp': data.get('timestamp'),
            'src_ip': src_ip,
            'dst_ip': dst_ip,
            'src_port': src_port,
            'dst_port': dst_port,
            'protocol': protocol,
            'severity': alert.get('severity'),
            'signature': alert.get('signature'),
            'category': alert.get('category'),
            'action': alert.get('action'),
            'raw_json': data
        }

    def send_to_kafka(self, data):
        try:
            self.producer.send(self.topic, value=data)
            self.producer.flush()
            logger.info(f"Sent alert to Kafka: {data.get('signature')}")
        except KafkaError as e:
            logger.error(f"Error sending to Kafka: {e}")


def main():
    bootstrap_servers = 'kafka:9092'
    topic = 'malicious_traffic'
    file_path = '/var/log/suricata/eve.json'

    producer = KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        retries=3
    )

    event_handler = EveJsonHandler(file_path, producer, topic)
    observer = Observer()
    observer.schedule(event_handler, path='/var/log/suricata', recursive=False)
    observer.start()

    logger.info("Suricata log producer started")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        producer.close()

    observer.join()


if __name__ == '__main__':
    main()
