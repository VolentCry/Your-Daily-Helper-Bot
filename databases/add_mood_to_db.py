# add_mood_to_db.py
import sqlite3
from datetime import datetime

# --- Константы ---
DB_PATH = "databases/mood_base.db" # Путь к файлу базы данных

def connect_db() -> sqlite3.Connection:
    """Подключается к базе данных и создает таблицы, если их нет."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Таблица для хранения записей о настроении
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS moods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            mood_id INTEGER NOT NULL
        )
    ''')
    # Таблица для хранения настроек (время отчетов и т.д.)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    conn.commit()
    return conn

def add_mood_to_db(mood_id: int):
    """Добавляет запись о настроении в базу данных."""
    conn = connect_db()
    cursor = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('INSERT INTO moods (timestamp, mood_id) VALUES (?, ?)', (timestamp, mood_id))
    conn.commit()
    conn.close()

def get_moods_from_db() -> list:
    """Получает все записи о настроении из базы данных."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT timestamp, mood_id FROM moods')
    rows = cursor.fetchall()
    conn.close()
    return rows
