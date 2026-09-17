import random
import string


def generate_order_number() -> str:
    """Generate a unique order number like VV-2024-XXXXX."""
    from datetime import datetime
    year = datetime.now().year
    suffix = ''.join(random.choices(string.digits, k=6))
    return f"VV-{year}-{suffix}"


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    import re
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = re.sub(r'^-+|-+$', '', text)
    return text


generate_slug = slugify


def format_price(amount: float) -> str:
    """Format price in Indian format."""
    return f"₹{amount:,.0f}"


def calculate_discount(original: float, discounted: float) -> int:
    """Calculate discount percentage."""
    if original <= 0:
        return 0
    return int(((original - discounted) / original) * 100)


def get_image_url(url: str | None) -> str:
    """
    Resolve image path or URL to a valid browser-accessible static URL or external URL.
    - Handles external URLs (http://, https://, data:)
    - Handles static paths (/static/images/..., images/..., uploads/...)
    - Handles bare filenames (e.g. 'saree1.jpg' -> '/static/images/saree1.jpg')
    - Handles Windows paths (app\\static\\images\\... -> /static/images/...)
    - Falls back to '/static/images/placeholder.jpg' if None, empty, or invalid
    """
    if not url:
        return "/static/images/placeholder.jpg"

    url_str = str(url).strip().replace("\\", "/")
    if not url_str or url_str.lower() in ("none", "null", "undefined", "false", ""):
        return "/static/images/placeholder.jpg"

    if url_str.startswith(("http://", "https://", "data:")):
        return url_str

    if url_str.startswith("app/static/"):
        url_str = url_str[4:]
    elif url_str.startswith("/app/static/"):
        url_str = url_str[5:]

    if url_str.startswith("/static/"):
        return url_str

    if url_str.startswith("static/"):
        return f"/{url_str}"

    clean_url = url_str.lstrip("/")
    if clean_url.startswith("images/") or clean_url.startswith("uploads/"):
        return f"/static/{clean_url}"

    return f"/static/images/{clean_url}"

