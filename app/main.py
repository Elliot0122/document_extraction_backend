from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import boto3
import json
import uuid
import os
from typing import Dict
from botocore.exceptions import ClientError
from . import config

app = FastAPI()

# Initialize global variables for AWS clients
s3 = None
textract = None

def init_aws_clients():
    """Initialize or reinitialize AWS clients."""
    global s3, textract
    s3 = boto3.client('s3',
        aws_access_key_id=config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
        region_name=config.AWS_REGION
    )
    textract = boto3.client('textract',
        aws_access_key_id=config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
        region_name=config.AWS_REGION
    )

# Initialize AWS clients on startup
init_aws_clients()

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

@app.post("/upload/")
async def upload_document(file: UploadFile = File(...)):
    """Uploads a document to S3 and returns a file ID for future reference."""
    try:
        validate_file(file)
        
        file_id = str(uuid.uuid4())
        file_content = await file.read()
        
        # Upload to S3
        s3_key = f"documents/{file_id}/{file.filename}"
        s3.put_object(
            Bucket=config.S3_BUCKET_NAME,
            Key=s3_key,
            Body=file_content
        )
        
        return {
            "message": "File uploaded successfully",
            "file_id": file_id,
            "filename": file.filename
        }
        
    except HTTPException as e:
        raise e
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query/")
async def query_document(file_id: str = Form(...), user_query: str = Form(...)):
    """Processes the document from S3 based on user queries."""
    try:
        # Get the list of files in the document's directory
        response = s3.list_objects_v2(
            Bucket=config.S3_BUCKET_NAME,
            Prefix=f"documents/{file_id}/"
        )
        
        if 'Contents' not in response or not response['Contents']:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get the first file in the directory
        s3_key = response['Contents'][0]['Key']
        
        # Get the file from S3
        s3_response = s3.get_object(Bucket=config.S3_BUCKET_NAME, Key=s3_key)
        file_content = s3_response['Body'].read()
        
        # Call Textract Queries API
        textract_response = textract.analyze_document(
            Document={'Bytes': file_content},
            FeatureTypes=['QUERIES'],
            QueriesConfig={
                'Queries': [
                    {'Text': user_query, 'Alias': 'user_query'}
                ]
            }
        )
        
        # Extract the answer from Textract response
        for block in textract_response.get("Blocks", []):
            if block.get("BlockType") == "QUERY_RESULT":
                return {
                    "query": user_query,
                    "answer": block["Text"],
                    "confidence": block.get("Confidence", 0)
                }
        
        return {
            "query": user_query,
            "answer": "No relevant answer found.",
            "confidence": 0
        }
        
    except HTTPException as e:
        raise e
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
