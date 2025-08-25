import uuid
import logging
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from app.schemas.ingestion import IngestResponse
from app.schemas.retrieval import RetrieveRequest, RetrieveResponse
from app.schemas.job import Job, JobListResponse
from app.utils.file_utils import save_uploaded_file
from app.workers.ingestion import process_ingestion
from app.utils.db_utils import add_job, get_job_status, get_all_jobs, get_job
from app.services.retrieval_service import RetrievalService

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

    file_path = save_uploaded_file(file,kb_name)
    logger.info(f"File saved to temporary path: {file_path}")

    # Save uuid to track the ingestion job
    job_id = str(uuid.uuid4())
    status = "in_queue"
    timestamp = datetime.now()
    add_job(job_id, status, kb_name, timestamp)
    logger.info(f"Job created with ID: {job_id}")

    background_tasks.add_task(process_ingestion, file_path, job_id)

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

@router.get("/jobs", response_model=JobListResponse)
async def list_jobs():
    """Lists all ingestion jobs."""
    logger.info("Received request to list all jobs.")
    jobs = get_all_jobs()
    return JobListResponse(jobs=jobs)

@router.get("/job/{job_id}", response_model=Job)
async def get_job_details(job_id: str):
    """Gets the details of a specific job."""
    logger.info(f"Received request for job details for job ID: {job_id}")
    job = get_job(job_id)
    if job is None:
        logger.warning(f"Job ID not found: {job_id}")
        raise HTTPException(status_code=404, detail="Job not found.")
    return job

@router.post("/retrieve", response_model=RetrieveResponse)
async def retrieve_from_kb(request: RetrieveRequest):
    """Retrieves information from a knowledge base."""
    logger.info(f"Received retrieval request for collection: {request.collection_name}")
    retrieval_service = RetrievalService()
    response = retrieval_service.retrieve(request.query, request.collection_name)
    return RetrieveResponse(response=response)