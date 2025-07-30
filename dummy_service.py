from __future__ import annotations

import base64
import os
import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import FileResponse

MODEL_SIZE = os.getenv("MODEL_SIZE", "dummy")
NUM_GPUS = int(os.getenv("NUM_GPUS", "0"))
OUT_DIR = Path(os.getenv("OUT_DIR", "/tmp/outputs")).expanduser()
OUT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Dummy Video2World Service",
    version="0.2.0",
    summary="Stub wrapper exposing a vLLM-style API for video generation",
)

class GenerateRequest(BaseModel):
    prompt: str
    image: str  # base64-encoded image data
    negative_prompt: str = ""
    guidance: float = 7.0

class GenerateResponse(BaseModel):
    video_path: str


def _create_placeholder_video(path: Path) -> None:
    """Create a zero-byte MP4 file at *path* as a stand-in for real output."""
    path.touch(exist_ok=False)


@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    if not req.image:
        raise HTTPException(status_code=422, detail="Image data required")

    try:
        image_bytes = base64.b64decode(req.image)
    except Exception:
        raise HTTPException(status_code=422, detail="Image must be base64 encoded")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_in:
        tmp_in.write(image_bytes)
        tmp_in.flush()
        tmp_input_path = tmp_in.name

    file_id = f"{uuid.uuid4()}.mp4"
    video_path = OUT_DIR / file_id
    _create_placeholder_video(video_path)

    try:
        os.remove(tmp_input_path)
    except OSError:
        pass

    return {"video_path": file_id}


@app.get("/download/{file_id}")
def download(file_id: str):
    path = OUT_DIR / file_id
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type="video/mp4")


@app.get("/ping")
def ping():
    return {
        "status": "ok",
        "model_size": MODEL_SIZE,
        "num_gpus": NUM_GPUS,
    }
