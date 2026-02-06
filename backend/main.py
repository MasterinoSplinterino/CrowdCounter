import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from db.database import init_db, get_db, DATABASE_PATH
from detector.manager import DetectionManager
from api import (
    rooms_router,
    counts_router,
    settings_router,
    preview_router,
    ws_router,
    test_router,
)
from api.settings import set_detection_manager as set_settings_manager
from api.preview import set_detection_manager as set_preview_manager
from api.test import set_detection_manager as set_test_manager
from api.ws import broadcast_count_update
from api.counts import save_count

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()
detection_manager: DetectionManager = None


async def on_count_update(
    room_id: str,
    count: int,
    raw_count: int,
    occupancy: float,
    frame_base64: str = None
):
    """Callback when detection produces a new count."""
    # Save to database
    async for db in get_db():
        await save_count(db, room_id, count, raw_count, occupancy)

    # Broadcast via WebSocket
    await broadcast_count_update(room_id, count, raw_count, occupancy, frame_base64)


async def load_rooms_from_db():
    """Load active rooms from database and start detection."""
    async for db in get_db():
        cursor = await db.execute(
            "SELECT id, camera_url, capacity, is_active FROM rooms WHERE is_active = 1"
        )
        rooms = await cursor.fetchall()

        for room in rooms:
            await detection_manager.add_room(
                room_id=room["id"],
                camera_url=room["camera_url"],
                capacity=room["capacity"],
                is_active=bool(room["is_active"])
            )
        logger.info(f"Loaded {len(rooms)} active rooms from database")


async def load_settings_from_db():
    """Load detection settings from database."""
    async for db in get_db():
        cursor = await db.execute("SELECT key, value FROM settings")
        rows = await cursor.fetchall()

        settings_dict = {}
        for row in rows:
            key = row["key"]
            value = row["value"]
            if key in ["confidence_threshold", "smoothing_alpha"]:
                settings_dict[key] = float(value)
            elif key in ["detection_interval", "imgsz"]:
                settings_dict[key] = int(value)
            else:
                settings_dict[key] = value

        if settings_dict:
            await detection_manager.update_settings(settings_dict)
        logger.info("Loaded detection settings from database")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global detection_manager

    # Initialize database
    await init_db(settings.database_path)
    logger.info(f"Database initialized at {settings.database_path}")

    # Initialize detection manager
    detection_manager = DetectionManager(device=settings.device)
    detection_manager.set_count_callback(on_count_update)

    # Set manager references for API routes
    set_settings_manager(detection_manager)
    set_preview_manager(detection_manager)
    set_test_manager(detection_manager)

    # Load settings from DB
    await load_settings_from_db()

    # Initialize YOLO model
    await detection_manager.initialize(detection_manager.settings["model"])
    logger.info("Detection engine initialized")

    # Load and start room processing
    await load_rooms_from_db()

    yield

    # Shutdown
    await detection_manager.shutdown()
    logger.info("Application shutdown complete")


app = FastAPI(
    title="CrowdCount API",
    description="Real-time people counting system",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(rooms_router)
app.include_router(counts_router)
app.include_router(settings_router)
app.include_router(preview_router)
app.include_router(ws_router)
app.include_router(test_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload=False,
    )
