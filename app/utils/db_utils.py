import sqlite3
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DB_FILE = "jobs.db"
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", DB_FILE)

def init_db():
    """Initializes the database and creates the jobs table if it doesn't exist."""
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS jobs
            (job_id TEXT PRIMARY KEY, 
             status TEXT, 
             kb_name TEXT, 
             timestamp DATETIME)
        ''')
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error("Error initializing database.", exc_info=True)

def add_job(job_id, status, kb_name, timestamp):
    """Adds a new job to the database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO jobs (job_id, status, kb_name, timestamp) VALUES (?, ?, ?, ?)", 
                    (job_id, status, kb_name, timestamp))
        conn.commit()
        conn.close()
        logger.info(f"Added job {job_id} with status '{status}' to the database.")
    except Exception as e:
        logger.error(f"Error adding job {job_id} to the database.", exc_info=True)

def update_job_status(job_id, status):
    """Updates the status of a job."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE jobs SET status = ? WHERE job_id = ?", (status, job_id))
        conn.commit()
        conn.close()
        logger.info(f"Updated job {job_id} status to '{status}'.")
    except Exception as e:
        logger.error(f"Error updating job {job_id} status.", exc_info=True)

def get_job_status(job_id):
    """Gets the status of a job."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT status FROM jobs WHERE job_id = ?", (job_id,))
        result = c.fetchone()
        conn.close()
        if result:
            logger.info(f"Retrieved status for job {job_id}: '{result[0]}'")
            return result[0]
        else:
            logger.warning(f"Job {job_id} not found in the database.")
            return None
    except Exception as e:
        logger.error(f"Error getting status for job {job_id}.", exc_info=True)
        return None

def get_all_jobs():
    """Gets all jobs from the database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT job_id, status, kb_name, timestamp FROM jobs ORDER BY timestamp DESC")
        results = c.fetchall()
        conn.close()
        logger.info(f"Retrieved {len(results)} jobs from the database.")
        return [dict(row) for row in results]
    except Exception as e:
        logger.error("Error getting all jobs.", exc_info=True)
        return []

def get_job(job_id):
    """Gets a job by its ID."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT job_id, status, kb_name, timestamp FROM jobs WHERE job_id = ?", (job_id,))
        result = c.fetchone()
        conn.close()
        if result:
            logger.info(f"Retrieved job {job_id}.")
            return dict(result)
        else:
            logger.warning(f"Job {job_id} not found in the database.")
            return None
    except Exception as e:
        logger.error(f"Error getting job {job_id}.", exc_info=True)
        return None