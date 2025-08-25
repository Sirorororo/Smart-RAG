import uuid
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from app.schemas.ingestion import IngestResponse
from app.utils.file_utils import save_temp_file
from app.workers.ingestion import process_ingestion

router = APIRouter()

@router.post("/ingest", response_model=IngestResponse)
async def ingest_pdf(
    kb_name: str,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    # Implement the ingestion logic

    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    temp_path = save_temp_file(file,kb_name)

    background_tasks.add_task(process_ingestion, temp_path)

    return IngestResponse(status="in_queue", kb_name=kb_name)

