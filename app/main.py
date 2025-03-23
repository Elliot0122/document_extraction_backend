from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uuid
from .services.aws_service import AWSService
from .services.cleanup_service import CleanupService
from .utils.file_validator import validate_file
import os

app = FastAPI()

# Get allowed origins from environment variable or use default
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
aws_service = AWSService()
cleanup_service = CleanupService(aws_service)

@app.on_event("startup")
async def startup_event():
    """Start services on application startup."""
    cleanup_service.start()

@app.on_event("shutdown")
async def shutdown_event():
    """Stop services on application shutdown."""
    cleanup_service.stop()

@app.post("/upload/")
async def upload_document(file: UploadFile = File(...)):
    """Uploads a document to S3 and returns a file ID for future reference."""
    try:
        validate_file(file)
        
        file_id = str(uuid.uuid4())
        file_content = await file.read()
        
        return aws_service.upload_file(file_content, file_id, file.filename)
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query/")
async def query_document(file_id: str = Form(...), user_query: str = Form(...)):
    """Processes the document from S3 based on user queries."""
    try:
        file_content = aws_service.get_file(file_id)
        return aws_service.analyze_document(file_content, user_query)
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
