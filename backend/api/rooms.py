from fastapi import APIRouter, Depends, HTTPException
from typing import List
import aiosqlite

from db.database import get_db
from db.models import (
    Room, RoomCreate, RoomUpdate, RoomWithCount,
    get_occupancy_status
)

router = APIRouter(prefix="/api/rooms", tags=["rooms"])


@router.get("", response_model=List[RoomWithCount])
async def get_rooms(db: aiosqlite.Connection = Depends(get_db)):
    """Get all rooms with current count."""
    cursor = await db.execute("""
        SELECT r.*, c.count, c.raw_count, c.occupancy, c.timestamp as last_updated
        FROM rooms r
        LEFT JOIN (
            SELECT room_id, count, raw_count, occupancy, timestamp,
                   ROW_NUMBER() OVER (PARTITION BY room_id ORDER BY timestamp DESC) as rn
            FROM counts
        ) c ON r.id = c.room_id AND c.rn = 1
        ORDER BY r.name
    """)
    rows = await cursor.fetchall()

    rooms = []
    for row in rows:
        count = row["count"] or 0
        capacity = row["capacity"]
        occupancy = (count / capacity * 100) if capacity > 0 else 0

        rooms.append(RoomWithCount(
            id=row["id"],
            name=row["name"],
            capacity=row["capacity"],
            camera_url=row["camera_url"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            count=count,
            raw_count=row["raw_count"] or 0,
            occupancy_percent=round(occupancy, 1),
            status=get_occupancy_status(occupancy),
            last_updated=row["last_updated"],
        ))

    return rooms


@router.get("/{room_id}", response_model=RoomWithCount)
async def get_room(room_id: str, db: aiosqlite.Connection = Depends(get_db)):
    """Get room details with current count."""
    cursor = await db.execute("""
        SELECT r.*, c.count, c.raw_count, c.occupancy, c.timestamp as last_updated
        FROM rooms r
        LEFT JOIN (
            SELECT room_id, count, raw_count, occupancy, timestamp
            FROM counts
            WHERE room_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        ) c ON r.id = c.room_id
        WHERE r.id = ?
    """, (room_id, room_id))
    row = await cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Room not found")

    count = row["count"] or 0
    capacity = row["capacity"]
    occupancy = (count / capacity * 100) if capacity > 0 else 0

    return RoomWithCount(
        id=row["id"],
        name=row["name"],
        capacity=row["capacity"],
        camera_url=row["camera_url"],
        is_active=bool(row["is_active"]),
        created_at=row["created_at"],
        count=count,
        raw_count=row["raw_count"] or 0,
        occupancy_percent=round(occupancy, 1),
        status=get_occupancy_status(occupancy),
        last_updated=row["last_updated"],
    )


@router.post("", response_model=Room, status_code=201)
async def create_room(room: RoomCreate, db: aiosqlite.Connection = Depends(get_db)):
    """Create a new room."""
    try:
        await db.execute("""
            INSERT INTO rooms (id, name, capacity, camera_url, is_active)
            VALUES (?, ?, ?, ?, ?)
        """, (room.id, room.name, room.capacity, room.camera_url, room.is_active))
        await db.commit()
    except aiosqlite.IntegrityError:
        raise HTTPException(status_code=400, detail="Room with this ID already exists")

    cursor = await db.execute("SELECT * FROM rooms WHERE id = ?", (room.id,))
    row = await cursor.fetchone()

    return Room(
        id=row["id"],
        name=row["name"],
        capacity=row["capacity"],
        camera_url=row["camera_url"],
        is_active=bool(row["is_active"]),
        created_at=row["created_at"],
    )


@router.put("/{room_id}", response_model=Room)
async def update_room(
    room_id: str,
    room: RoomUpdate,
    db: aiosqlite.Connection = Depends(get_db)
):
    """Update room settings."""
    cursor = await db.execute("SELECT * FROM rooms WHERE id = ?", (room_id,))
    existing = await cursor.fetchone()

    if not existing:
        raise HTTPException(status_code=404, detail="Room not found")

    update_fields = []
    values = []

    if room.name is not None:
        update_fields.append("name = ?")
        values.append(room.name)
    if room.capacity is not None:
        update_fields.append("capacity = ?")
        values.append(room.capacity)
    if room.camera_url is not None:
        update_fields.append("camera_url = ?")
        values.append(room.camera_url)
    if room.is_active is not None:
        update_fields.append("is_active = ?")
        values.append(room.is_active)

    if update_fields:
        values.append(room_id)
        await db.execute(
            f"UPDATE rooms SET {', '.join(update_fields)} WHERE id = ?",
            values
        )
        await db.commit()

    cursor = await db.execute("SELECT * FROM rooms WHERE id = ?", (room_id,))
    row = await cursor.fetchone()

    return Room(
        id=row["id"],
        name=row["name"],
        capacity=row["capacity"],
        camera_url=row["camera_url"],
        is_active=bool(row["is_active"]),
        created_at=row["created_at"],
    )


@router.delete("/{room_id}", status_code=204)
async def delete_room(room_id: str, db: aiosqlite.Connection = Depends(get_db)):
    """Delete a room and its history."""
    cursor = await db.execute("SELECT id FROM rooms WHERE id = ?", (room_id,))
    if not await cursor.fetchone():
        raise HTTPException(status_code=404, detail="Room not found")

    await db.execute("DELETE FROM counts WHERE room_id = ?", (room_id,))
    await db.execute("DELETE FROM rooms WHERE id = ?", (room_id,))
    await db.commit()
