from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from lib.aws_service import aws_service
from mangum import Mangum
import base64
import json
import uuid
import os

def lambda_handler(event, context):
    """Handle API Gateway events for document processing."""
    try:
        # Parse the HTTP method and path
        http_method = event['httpMethod']
        path = event['path']
        
        # Handle different endpoints
        if path == '/upload' and http_method == 'POST':
            return handle_upload(event)
        elif path == '/query' and http_method == 'POST':
            return handle_query(event)
        else:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Not found'})
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

# def handle_upload(event):
#     """Handle file upload."""
#     try:
        

#         # Generate file ID and upload
#         file_id = str(uuid.uuid4())
#         response = aws_service.upload_file(file_content, file_id, file.filename)
        
#         return response
        
#     except Exception as e:
#         return {
#             'statusCode': 400,
#             'body': json.dumps({'error': str(e)}),
#             'headers': {
#                 'Content-Type': 'application/json',
#                 'Access-Control-Allow-Origin': '*'
#             }
#         }

def handle_upload(event):
    """Uses FastAPI + Mangum internally to handle file upload."""
    app = FastAPI()

    ALLOWED_FILE_TYPES = [".png", ".jpg", ".jpeg", ".pdf"]
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    @app.post("/upload")
    async def upload(file: UploadFile = File(...)):
        content = await file.read()

        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large")

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_FILE_TYPES:
            raise HTTPException(status_code=400, detail="File type not allowed")

        file_id = str(uuid.uuid4())
        result = aws_service.upload_file(content, file_id, file.filename)

        return JSONResponse(content={"status": "success", "data": result}, status_code=200)

    # Use Mangum to adapt FastAPI app to Lambda event
    handler = Mangum(app)

    try:
        return handler(event, None)
    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"Internal server error: {str(e)}"
        }

def handle_query(event):
    """Handle document query."""
    try:
        # Parse the request body
        body = json.loads(event['body'])
        file_id = body.get('file_id')
        user_query = body.get('user_query')
        
        if not file_id or not user_query:
            raise ValueError("Missing required parameters")
            
        # Get file from S3
        file_content = aws_service.get_file(file_id)
        
        # Analyze the document
        analysis_result = aws_service.analyze_document(file_content, user_query)
        
        # Combine analysis result with the image URL
        response = {
            "query": analysis_result["query"],
            "answer": analysis_result["answer"],
            "confidence": analysis_result["confidence"],
            "geometry": analysis_result["geometry"]
        }
        
        return {
            'statusCode': 200,
            'body': json.dumps(response),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
        
    except FileNotFoundError:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'File not found'}),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }