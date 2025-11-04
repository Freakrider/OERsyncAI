from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter()

@router.get("/media/{job_id}/{file_path:path}")
async def serve_media_file(job_id: str, file_path: str):
    base_path = Path("/tmp")
    matching_dirs = list(base_path.glob(f"mbz_extract_{job_id}_*/extracted/files"))

    if not matching_dirs:
        raise HTTPException(status_code=404, detail="Media directory not found")

    media_dir = matching_dirs[0]  # First match
    # Split and strip filename (keep only folder and file_id)
    parts = Path(file_path).parts
    if len(parts) < 2:
        raise HTTPException(status_code=400, detail="Invalid file path")

    # Use only the last 2 parts before filename: e.g., a1/a101b33...
    safe_path = Path(*parts[:2])
    target_file = media_dir / safe_path

    if not target_file.exists() or not target_file.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(target_file)

