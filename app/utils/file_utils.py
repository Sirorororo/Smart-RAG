import os
import uuid
from fastapi import UploadFile

BASE_STORAGE = "storage"

def save_temp_file(file: UploadFile, kb_name: str) -> str:
    """
    Save an uploaded file to a temporary directory with a unique filename.
    Returns the absolute file path.
    """

    kb_dir = os.path.join(BASE_STORAGE, kb_name)
    os.makedirs(kb_dir, exist_ok=True)

    # Generate unique filename
    unique_name = f"{uuid.uuid4()}_{file.filename}"
    temp_path = os.path.join(kb_dir, unique_name)

    # Save file in chunks (safer than reading all at once for big PDFs)
    with open(temp_path, "wb") as f:
        while chunk := file.file.read(1024 * 1024):  # 1MB chunks
            f.write(chunk)

    # Reset file pointer (important if file object will be reused later)
    file.file.seek(0)

    return temp_path
