from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .services.aws_service import AWSService
from .services.cleanup_service import CleanupService
from .utils.image_processing import circle_the_info_on_image
from app import config
import uuid
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

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Uploads a document to S3 and returns a file ID for future reference."""
    try:
        # Read file content first
        file_content = await file.read()
        
        # Validate file size and type
        file_size = len(file_content)
        if file_size > config.MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large")
        
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in config.ALLOWED_FILE_TYPES:
            raise HTTPException(status_code=400, detail="File type not allowed")

        # Generate file ID and upload
        file_id = str(uuid.uuid4())
        response = aws_service.upload_file(file_content, file_id, file.filename)
        
        return response
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def query_document(file_id: str = Form(...), user_query: str = Form(...)):
    """Processes the document from S3 based on user queries and returns both analysis and marked image."""
    try:
        # Get file from S3
        file_content = aws_service.get_file(file_id)
        
        # Analyze the document
        analysis_result = aws_service.analyze_document(file_content, user_query)
        
        # Get the geometry from analysis result
        geometry = analysis_result.get("geometry")
        
        # Draw circle on the image
        base64_image = circle_the_info_on_image(file_content, geometry)
        
        # Combine analysis result with the image
        return {
            "query": analysis_result["query"],
            "answer": analysis_result["answer"],
            "confidence": analysis_result["confidence"],
            "image": {
                "content": base64_image,
                "content_type": "image/png"
            }
        }
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
