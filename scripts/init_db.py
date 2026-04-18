import pymysql
from datetime import datetime, timedelta
import random

pymysql.install_as_MySQLdb()


def create_database():
    from backend.config import Config

    connection = pymysql.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DATABASE}")
        connection.commit()
    finally:
        connection.close()


def init_database():
    from backend.app import app
    from backend.models import db

    with app.app_context():
        db.create_all()


if __name__ == '__main__':
    create_database()
    init_database()
