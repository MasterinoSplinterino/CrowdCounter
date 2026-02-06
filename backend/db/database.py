import aiosqlite
from pathlib import Path
from typing import AsyncGenerator
import asyncio

DATABASE_PATH: str = "./data/crowdcount.db"

_db_lock = asyncio.Lock()


async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    async with _db_lock:
        db = await aiosqlite.connect(DATABASE_PATH)
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys=ON")
        try:
            yield db
        finally:
            await db.close()


async def init_db(db_path: str = None) -> None:
    global DATABASE_PATH
    if db_path:
        DATABASE_PATH = db_path

    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys=ON")

        await db.execute("""
            CREATE TABLE IF NOT EXISTS rooms (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                capacity INTEGER NOT NULL,
                camera_url TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS counts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id TEXT NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
                count INTEGER NOT NULL,
                raw_count INTEGER NOT NULL,
                occupancy REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_counts_room_time
            ON counts(room_id, timestamp)
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        # Insert default settings if not exist
        default_settings = [
            ("model", "yolo26n.pt"),
            ("confidence_threshold", "0.35"),
            ("detection_interval", "15"),
            ("smoothing_alpha", "0.3"),
            ("imgsz", "640"),
        ]

        for key, value in default_settings:
            await db.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )

        await db.commit()
