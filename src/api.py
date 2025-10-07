import os
import secrets
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import existing remix logic
from .mix_images import remix_images, generate_table_prompt

load_dotenv()

app = FastAPI(
    title="RAUW Tafel Designer API",
    description="AI-powered custom table designer - combine shapes, bases, and wood finishes",
    version="1.0.0"
)

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Enable CORS for external website integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://rauw.nl", "https://www.rauw.nl", "http://localhost:3000"],  # Production domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers middleware
@app.middleware("http")
async def security_middleware(request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Base directories
BASE_DIR = Path(__file__).parent.parent
CATEGORIES = ["vorm", "onderstel", "kleur"]
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Security configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def safe_filename(filename: str) -> str:
    """Prevent path traversal attacks by returning only the basename."""
    return Path(filename).name


async def validate_file_size(file: UploadFile):
    """Validate uploaded file doesn't exceed size limit."""
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(413, "File exceeds 10MB limit")
    await file.seek(0)
    return file


@app.get("/")
async def root():
    """API health check and info."""
    return {
        "name": "RAUW Tafel Designer API",
        "status": "operational",
        "docs": "/docs",
        "endpoints": {
            "list_images": "GET /api/categories/{category}",
            "preview_image": "GET /api/images/{category}/{filename}",
            "generate_table": "POST /api/generate",
            "get_result": "GET /api/output/{filename}"
        }
    }


@app.get("/api/categories/{category}")
@limiter.limit("30/minute")
async def list_category_images(request: Request, category: str):
    """List all available images in a category (vorm/onderstel/kleur)."""
    if category not in CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Must be one of: {', '.join(CATEGORIES)}"
        )

    category_dir = BASE_DIR / category
    if not category_dir.exists():
        raise HTTPException(status_code=404, detail=f"Category directory not found")

    # Get all image files
    images = sorted([
        f.name for f in category_dir.iterdir()
        if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png']
    ])

    return {
        "category": category,
        "images": images,
        "count": len(images)
    }


@app.get("/api/images/{category}/{filename}")
@limiter.limit("60/minute")
async def get_category_image(request: Request, category: str, filename: str):
    """Serve a preview image from vorm/onderstel/kleur directories."""
    if category not in CATEGORIES:
        raise HTTPException(status_code=400, detail="Invalid category")

    file_path = BASE_DIR / category / safe_filename(filename)
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(file_path)


@app.post("/api/generate")
@limiter.limit("5/hour")
async def generate_table(
    request: Request,
    vorm: str = Form(..., description="Filename from vorm/ directory (e.g., 'rond.jpeg')"),
    onderstel: str = Form(..., description="Filename from onderstel/ directory"),
    kleur: str = Form(..., description="Filename from kleur/ directory"),
    room_photo: Optional[UploadFile] = File(None, description="Optional room photo to place table in")
):
    """
    Generate a custom table by combining vorm, onderstel, kleur, and optionally a room photo.

    Returns the URL to the generated image.
    """
    # Validate input files exist
    vorm_path = BASE_DIR / "vorm" / safe_filename(vorm)
    onderstel_path = BASE_DIR / "onderstel" / safe_filename(onderstel)
    kleur_path = BASE_DIR / "kleur" / safe_filename(kleur)

    for path, name in [(vorm_path, "vorm"), (onderstel_path, "onderstel"), (kleur_path, "kleur")]:
        if not path.exists():
            raise HTTPException(status_code=404, detail=f"{name} file not found: {path.name}")

    # Prepare image paths
    image_paths = [str(vorm_path), str(onderstel_path), str(kleur_path)]

    # Handle optional room photo upload
    room_photo_path = None
    if room_photo:
        # Validate file size
        await validate_file_size(room_photo)

        # Save uploaded room photo temporarily with secure filename
        room_photo_path = OUTPUT_DIR / f"temp_room_{secrets.token_hex(8)}.jpg"
        with open(room_photo_path, "wb") as f:
            content = await room_photo.read()
            f.write(content)
        image_paths.append(str(room_photo_path))

    # Generate appropriate prompt
    prompt = generate_table_prompt(with_room=bool(room_photo))

    # Check API key
    if not os.environ.get("GEMINI_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY not configured. Please set environment variable."
        )

    try:
        # Call existing remix_images function
        remix_images(
            image_paths=image_paths,
            prompt=prompt,
            output_dir=str(OUTPUT_DIR)
        )

        # Find the most recent output file
        output_files = sorted(
            OUTPUT_DIR.glob("remixed_image_*"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        if not output_files:
            raise HTTPException(status_code=500, detail="Image generation failed - no output produced")

        latest_output = output_files[0]

        # Cleanup temporary room photo
        if room_photo_path and room_photo_path.exists():
            room_photo_path.unlink()

        return JSONResponse({
            "success": True,
            "output_url": f"/api/output/{latest_output.name}",
            "filename": latest_output.name,
            "message": "Table generated successfully"
        })

    except Exception as e:
        # Cleanup on error
        if room_photo_path and room_photo_path.exists():
            room_photo_path.unlink()
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@app.get("/api/output/{filename}")
async def get_output_image(filename: str):
    """Serve a generated table image from the output directory."""
    # Sanitize filename to prevent path traversal
    safe_name = safe_filename(filename)

    if not safe_name.startswith("remixed_image_"):
        raise HTTPException(status_code=403, detail="Access denied")

    file_path = OUTPUT_DIR / safe_name

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Output image not found")

    return FileResponse(file_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
