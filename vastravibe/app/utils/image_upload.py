import os
import io
import re
import uuid
import shutil
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException
from PIL import Image
from app.config import settings

# Upload Directories
BASE_APP_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_APP_DIR / "static"
PRODUCT_IMAGES_DIR = STATIC_DIR / "images" / "products"
PRODUCT_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Also ensure upload dirs exist
UPLOAD_DIR = STATIC_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/pjpeg",
    "image/x-png"
}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def sanitize_slug(name: str) -> str:
    """Create a safe alphanumeric filename slug."""
    clean = re.sub(r'[^a-zA-Z0-9\s-]', '', str(name)).strip().lower()
    clean = re.sub(r'[\s_-]+', '-', clean)
    clean = clean.strip('-')
    return clean[:30] if clean else "product"


def validate_and_read_image(file: UploadFile) -> tuple[bytes, str]:
    """
    Validate uploaded image:
    1. Checks extension against allowed formats (.jpg, .jpeg, .png, .webp)
    2. Validates maximum file size of 5 MB
    3. Validates actual image binary content using Pillow
    Returns the file bytes and validated extension.
    """
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="Please select an image.")

    filename = file.filename
    ext = Path(filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only JPG, JPEG, PNG and WEBP images are allowed.")

    # Read content into memory for size and content inspection
    try:
        file.file.seek(0)
        contents = file.file.read()
    except Exception:
        raise HTTPException(status_code=400, detail="Image upload failed. Please try again.")

    if not contents or len(contents) == 0:
        raise HTTPException(status_code=400, detail="Please select an image.")

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Image size must be less than 5 MB.")

    # Verify actual image content using Pillow
    try:
        img_buffer = io.BytesIO(contents)
        with Image.open(img_buffer) as img:
            img_format = img.format
            img.verify()

        if img_format not in ("JPEG", "PNG", "WEBP"):
            raise HTTPException(status_code=400, detail="Only JPG, JPEG, PNG and WEBP images are allowed.")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Only JPG, JPEG, PNG and WEBP images are allowed.")

    return contents, ext


def save_product_image(file: UploadFile, product_title: Optional[str] = None) -> str:
    """
    Save an uploaded product image inside static/images/products/.
    - Validates file type and size
    - Validates binary image content
    - Generates a collision-resistant unique filename preserving extension
    - Saves image locally and returns relative path: /static/images/products/{filename}
    """
    contents, ext = validate_and_read_image(file)

    # Generate collision-safe filename: e.g. banarasi-saree-a82f91.jpg
    stem_slug = sanitize_slug(product_title or Path(file.filename).stem)
    unique_suffix = uuid.uuid4().hex[:6]
    unique_filename = f"{stem_slug}-{unique_suffix}{ext}"

    # Path traversal protection
    dest_path = (PRODUCT_IMAGES_DIR / unique_filename).resolve()
    if not str(dest_path).startswith(str(PRODUCT_IMAGES_DIR.resolve())):
        raise HTTPException(status_code=400, detail="Invalid file destination.")

    try:
        with open(dest_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Image upload failed. Please try again.")

    return f"/static/images/products/{unique_filename}"


def delete_product_image_file(image_url: Optional[str], db=None) -> None:
    """
    Safely delete local product image file if it is stored in /static/images/products/
    and not shared with other products in the database.
    """
    if not image_url or not str(image_url).startswith("/static/images/products/"):
        return

    filename = Path(image_url).name
    if not filename or filename == "placeholder.jpg":
        return

    # Check if another ProductImage is using this exact image URL
    if db is not None:
        try:
            from app.models.product_image import ProductImage
            active_count = db.query(ProductImage).filter(ProductImage.image_url == image_url).count()
            if active_count > 1:
                # Still shared with other products/images, do not delete
                return
        except Exception:
            pass

    file_path = PRODUCT_IMAGES_DIR / filename
    try:
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
    except Exception:
        pass


# ── Backward Compatibility Helpers ──

def save_upload_file(file: UploadFile, subfolder: str = "products") -> str:
    """Save uploaded file to local storage and return URL path."""
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS and ext != ".gif":
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
        try:
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
        except Exception:
            return save_upload_file(file, folder)
    else:
        return save_upload_file(file, folder)
