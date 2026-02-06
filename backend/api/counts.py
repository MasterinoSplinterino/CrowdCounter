from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from datetime import datetime, timedelta
import aiosqlite

from db.database import get_db
from db.models import Count, get_occupancy_status

router = APIRouter(prefix="/api/rooms", tags=["counts"])


@router.get("/{room_id}/current")
async def get_current_count(
    room_id: str,
    db: aiosqlite.Connection = Depends(get_db)
):
    """Get current count for a room."""
    # Check room exists
    cursor = await db.execute(
        "SELECT id, name, capacity FROM rooms WHERE id = ?",
        (room_id,)
    )
    room = await cursor.fetchone()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Get latest count
    cursor = await db.execute("""
        SELECT count, raw_count, occupancy, timestamp
        FROM counts
        WHERE room_id = ?
        ORDER BY timestamp DESC
        LIMIT 1
    """, (room_id,))
    row = await cursor.fetchone()

    count = row["count"] if row else 0
    raw_count = row["raw_count"] if row else 0
    occupancy = row["occupancy"] if row else 0.0
    timestamp = row["timestamp"] if row else None

    return {
        "room_id": room_id,
        "room_name": room["name"],
        "count": count,
        "raw_count": raw_count,
        "capacity": room["capacity"],
        "occupancy_percent": round(occupancy, 1),
        "status": get_occupancy_status(occupancy).value,
        "timestamp": timestamp,
    }


@router.get("/{room_id}/history", response_model=List[Count])
async def get_count_history(
    room_id: str,
    hours: int = Query(default=10, ge=1, le=72),
    db: aiosqlite.Connection = Depends(get_db)
):
    """Get count history for a room."""
    # Check room exists
    cursor = await db.execute("SELECT id FROM rooms WHERE id = ?", (room_id,))
    if not await cursor.fetchone():
        raise HTTPException(status_code=404, detail="Room not found")

    since = datetime.utcnow() - timedelta(hours=hours)

    cursor = await db.execute("""
        SELECT id, room_id, count, raw_count, occupancy, timestamp
        FROM counts
        WHERE room_id = ? AND timestamp >= ?
        ORDER BY timestamp ASC
    """, (room_id, since.isoformat()))

    rows = await cursor.fetchall()

    return [
        Count(
            id=row["id"],
            room_id=row["room_id"],
            count=row["count"],
            raw_count=row["raw_count"],
            occupancy=row["occupancy"],
            timestamp=row["timestamp"],
        )
        for row in rows
    ]


async def save_count(
    db: aiosqlite.Connection,
    room_id: str,
    count: int,
    raw_count: int,
    occupancy: float
):
    """Save a count record (internal use)."""
    await db.execute("""
        INSERT INTO counts (room_id, count, raw_count, occupancy)
        VALUES (?, ?, ?, ?)
    """, (room_id, count, raw_count, occupancy))
    await db.commit()
