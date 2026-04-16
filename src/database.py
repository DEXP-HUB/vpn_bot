import sqlite3
from pathlib import Path


def create_database(db_name: str = "sqlite.db") -> None:
    """
    Создает SQLite-базу данных и таблицы users/configs, если они еще не существуют.
    """
    db_path = Path(db_name)

    # Подключаемся к SQLite, включаем поддержку внешних ключей и создаем таблицы.
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT,
                last_name TEXT,
                user_name TEXT,
                telegram_id INTEGER NOT NULL UNIQUE
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS configs (
                config_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                allowed_ip TEXT,
                privatekey TEXT,
                publickey TEXT,
                config_name TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
            )
            """
        )
        connection.commit()