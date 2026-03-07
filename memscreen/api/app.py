"""FastAPI application for MemScreen Core API."""

from fastapi import FastAPI

from memscreen.version import __version__

from .routers.chat import router as chat_router
from .routers.models import router as models_router
from .routers.process import router as process_router
from .routers.recording import router as recording_router
from .routers.system import router as system_router
from .routers.video import router as video_router

app = FastAPI(
    title="MemScreen API",
    description="HTTP API for MemScreen core (Chat, Process, Recording, Video).",
    version=__version__,
)
app.include_router(chat_router)
app.include_router(models_router)
app.include_router(video_router)
app.include_router(recording_router)
app.include_router(process_router)
app.include_router(system_router)
