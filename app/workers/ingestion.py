import logging
import os
import pandas as pd
from app.utils.db_utils import update_job_status
from app.services.docling_service import create_df_from_pdf
from app.services.figure_service import process_figures
from app.services.vector_store_service import VectorStoreService

logger = logging.getLogger(__name__)

def process_ingestion(file_path: str, job_id: str):
    """Processes the ingestion of a file and updates the job status."""
    logger.info(f"Starting ingestion process for job ID: {job_id}")
    try:
        update_job_status(job_id, "processing")
        logger.info(f"Updated job {job_id} status to 'processing'")

        # Get base path from file_path
        base_path = os.path.dirname(os.path.dirname(file_path))
        
        # Create processed folder
        processed_dir = os.path.join(base_path, "processed")
        os.makedirs(processed_dir, exist_ok=True)
        logger.info(f"Created processed directory: {processed_dir}")

        # Create dataframe from PDF
        df_ingestion = create_df_from_pdf(file_path, processed_dir)

        # Process figures for each page
        updated_rows = []
        for _, row in df_ingestion.iterrows():
            updated_row = row.copy()
            content_dt, content_md = process_figures(
                row['contents_dt'],
                row['contents_md'],
                row['image.bytes'],
                row['extra.page_num']
            )
            updated_row['contents_dt'] = content_dt
            updated_row['contents_md'] = content_md
            updated_rows.append(updated_row)

        df_processed = pd.DataFrame(updated_rows)

        # Save processed dataframe to parquet
        file_name = os.path.basename(file_path)
        parquet_file_path = os.path.join(processed_dir, f"{os.path.splitext(file_name)[0]}.parquet")
        df_processed.to_parquet(parquet_file_path, engine="fastparquet", index=False)
        logger.info(f"Created parquet file: {parquet_file_path}")

        # Embed and store in Qdrant
        vector_store_service = VectorStoreService(collection_name=job_id)
        vector_store_service.embed_and_store(df_processed)

        update_job_status(job_id, "completed")
        logger.info(f"Updated job {job_id} status to 'completed'")
    except Exception as e:
        update_job_status(job_id, "failed")
        logger.error(f"Error processing {file_path} for job {job_id}: {e}", exc_info=True)
