import os
import uuid
import shutil
from pathlib import Path
from fastapi import UploadFile
from app.config import settings

UPLOAD_DIR = Path("app/static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def save_upload_file(file: UploadFile, subfolder: str = "products") -> str:
    """Save uploaded file to local storage and return URL path."""
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"File type {ext} not allowed")

    folder = UPLOAD_DIR / subfolder
    folder.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = folder / filename

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return f"/static/uploads/{subfolder}/{filename}"


def delete_file(url_path: str):
    """Delete a local file given its URL path."""
    if url_path and url_path.startswith("/static/uploads/"):
        file_path = Path("app") / url_path.lstrip("/")
        if file_path.exists():
            file_path.unlink()


def upload_to_cloudinary(file: UploadFile, folder: str = "products") -> str:
    """Upload file to Cloudinary if configured, else fall back to local."""
    if (settings.CLOUDINARY_CLOUD_NAME and
            settings.CLOUDINARY_API_KEY and
            settings.CLOUDINARY_API_SECRET):
        import cloudinary
        import cloudinary.uploader
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
        )
        result = cloudinary.uploader.upload(
            file.file,
            folder=f"vastravibe/{folder}",
            resource_type="image"
        )
        return result["secure_url"]
    else:
        return save_upload_file(file, folder)
