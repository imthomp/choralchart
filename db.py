"""Database access and schema management."""

import os
import sqlite3

DB_PATH = os.environ.get('DB_PATH', os.path.join(os.path.dirname(__file__), 'charts.db'))


def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    with get_db() as db:
        db.execute('''
            CREATE TABLE IF NOT EXISTS charts (
                id TEXT PRIMARY KEY,
                chart_data TEXT NOT NULL,
                part_order TEXT NOT NULL,
                part_grid TEXT,
                layout TEXT,
                singers_data TEXT,
                num_singers INTEGER,
                staggered TEXT,
                flipped TEXT,
                mixed TEXT,
                title TEXT,
                aisle_after TEXT,
                updated_at TEXT DEFAULT (datetime('now'))
            )
        ''')
        # Migrate existing databases that predate the aisle_after column
        existing_cols = {row[1] for row in db.execute('PRAGMA table_info(charts)')}
        if 'aisle_after' not in existing_cols:
            db.execute('ALTER TABLE charts ADD COLUMN aisle_after TEXT')
