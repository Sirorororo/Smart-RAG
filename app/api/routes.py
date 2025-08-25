import uuid
import logging
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from app.schemas.ingestion import IngestResponse
from app.utils.file_utils import save_temp_file
from app.workers.ingestion import process_ingestion
from app.utils.db_utils import add_job, get_job_status

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/ingest", response_model=IngestResponse)
async def ingest_pdf(
    kb_name: str,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    # Implement the ingestion logic
    logger.info(f"Received ingestion request for kb_name: {kb_name}")

    if file.content_type != "application/pdf":
        logger.warning(f"Invalid file type received: {file.content_type}")
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    temp_path = save_temp_file(file,kb_name)
    logger.info(f"File saved to temporary path: {temp_path}")

    # Save uuid to track the ingestion job
    job_id = str(uuid.uuid4())
    status = "in_queue"
    add_job(job_id, status)
    logger.info(f"Job created with ID: {job_id}")

    background_tasks.add_task(process_ingestion, temp_path, job_id)

    return IngestResponse(status=status, job_id=job_id)

@router.get("/ingest/status/{job_id}")
async def get_ingestion_status(job_id: str):
    """Gets the status of an ingestion job."""
    logger.info(f"Received status request for job ID: {job_id}")
    status = get_job_status(job_id)
    if status is None:
        logger.warning(f"Job ID not found: {job_id}")
        raise HTTPException(status_code=404, detail="Job not found.")
    logger.info(f"Returning status '{status}' for job ID: {job_id}")
    return {"job_id": job_id, "status": status}

