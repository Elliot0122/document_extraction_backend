import os
from fastapi import UploadFile, HTTPException
from .. import config

def validate_file(file: UploadFile):
    """Validate file type and size."""
    # Check file size
    file.file.seek(0, os.SEEK_END)
    size = file.file.tell()
    file.file.seek(0)
    
    if size > config.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")
    
    # Check file type
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in config.ALLOWED_FILE_TYPES:
        raise HTTPException(status_code=400, detail="File type not allowed") 