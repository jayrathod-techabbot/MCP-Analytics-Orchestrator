from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import FileResponse

from backend.config import settings
from backend.models.schemas import ErrorResponse, UploadResponse
from backend.utils.file_handler import (
    generate_file_id,
    get_upload_path,
    resolve_upload_path,
    validate_extension,
)
from backend.utils.logger import setup_logger

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

logger = setup_logger(__name__)

router = APIRouter(prefix="/api", tags=["files"])


@router.post(
    "/upload",
    response_model=UploadResponse,
    responses={400: {"model": ErrorResponse}, 413: {"model": ErrorResponse}},
)
async def upload_file(file: UploadFile):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    if not validate_extension(file.filename):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Allowed: .csv, .xlsx, .xls",
        )

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f} MB). Maximum: {settings.MAX_FILE_SIZE_MB} MB.",
        )

    file_id = generate_file_id()
    file_path = get_upload_path(file_id, file.filename)
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    file_path.write_bytes(content)
    logger.info("Uploaded file: %s -> %s", file.filename, file_path)

    try:
        ext = Path(file.filename).suffix.lower()
        if ext in (".xlsx", ".xls"):
            df = pd.read_excel(file_path, engine="openpyxl")
        else:
            df = pd.read_csv(file_path)

        preview = df.head(5).fillna("null").to_dict(orient="records")

        return UploadResponse(
            file_id=file_id,
            filename=file.filename,
            rows=df.shape[0],
            columns=df.shape[1],
            column_names=df.columns.tolist(),
            preview=preview,
        )
    except Exception as e:
        file_path.unlink(missing_ok=True)
        logger.error("Failed to parse uploaded file: %s", str(e))
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")


@router.get("/files/{file_id}")
async def get_file_metadata(file_id: str):
    file_path = resolve_upload_path(file_id)
    if file_path is None:
        raise HTTPException(status_code=404, detail="File not found.")

    ext = file_path.suffix.lower()
    if ext in (".xlsx", ".xls"):
        df = pd.read_excel(file_path, engine="openpyxl")
    else:
        df = pd.read_csv(file_path)

    return {
        "file_id": file_id,
        "filename": file_path.name,
        "rows": df.shape[0],
        "columns": df.shape[1],
        "column_names": df.columns.tolist(),
    }


@router.get("/exports/{filename}", tags=["exports"])
async def download_export(filename: str):
    if not filename.endswith(".xlsx") or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")

    file_path = (settings.EXPORTS_DIR / filename).resolve()

    if not str(file_path).startswith(str(settings.EXPORTS_DIR.resolve())):
        raise HTTPException(status_code=400, detail="Invalid file path.")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Export file not found.")

    logger.info("Serving export file: %s", file_path)
    return FileResponse(
        path=str(file_path),
        media_type=XLSX_MIME,
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/files/{file_id}")
async def delete_file(file_id: str):
    file_path = resolve_upload_path(file_id)
    if file_path is None:
        raise HTTPException(status_code=404, detail="File not found.")

    file_path.unlink(missing_ok=True)
    logger.info("Deleted file: %s", file_path)
    return {"message": "File deleted successfully."}
