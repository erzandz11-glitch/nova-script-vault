import sqlite3
import os
from datetime import datetime

class Deduplicator:
    def __init__(self, db_path="storage/harvest_history.sqlite"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS harvested_scripts (
                    id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    title TEXT NOT NULL,
                    author TEXT,
                    source_url TEXT,
                    download_url TEXT,
                    local_filename TEXT,
                    file_size INTEGER DEFAULT 0,
                    harvested_at TEXT NOT NULL,
                    audit_status TEXT DEFAULT 'unreviewed',
                    notes TEXT
                )
            """)
            conn.commit()

    def is_harvested(self, script_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM harvested_scripts WHERE id = ?", (script_id,))
            return cursor.fetchone() is not None

    def record_harvest(self, script_id: str, source: str, title: str, author: str = "",
                       source_url: str = "", download_url: str = "", local_filename: str = "",
                       file_size: int = 0, notes: str = "") -> bool:
        if self.is_harvested(script_id):
            return False
        
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO harvested_scripts 
                (id, source, title, author, source_url, download_url, local_filename, file_size, harvested_at, audit_status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'unreviewed', ?)
            """, (script_id, source, title, author, source_url, download_url, local_filename, file_size, now, notes))
            conn.commit()
            return True

    def get_all_harvested(self, limit: int = 50):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM harvested_scripts ORDER BY harvested_at DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def count_total(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM harvested_scripts")
            return cursor.fetchone()[0]
