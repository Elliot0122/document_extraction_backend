from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from lib.secrets import get_openai_api_key
from lib.openai_client import OpenAIClient
from lib.aws_service import aws_service
from mangum import Mangum
import json
import uuid
import os

def lambda_handler(event, context):
    """Handle API Gateway events for document processing."""
    try:
        http_method = event['httpMethod']
        path = event['path']

        # Define common CORS headers
        cors_headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "OPTIONS,POST"
        }

        # Handle CORS preflight request
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({'message': 'CORS preflight'})
            }

        # Handle actual requests
        if path == '/upload' and http_method == 'POST':
            response = handle_upload(event)
        elif path == '/query' and http_method == 'POST':
            response = handle_query(event)
        else:
            response = {
                'statusCode': 404,
                'body': json.dumps({'error': 'Not found'})
            }

        # Add CORS headers to the response if not already included
        if 'headers' not in response:
            response['headers'] = cors_headers
        else:
            response['headers'].update(cors_headers)

        return response

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'error': str(e)})
        }

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
        user_queries = body.get('user_queries', [])
        
        if not file_id or not user_queries:
            raise ValueError("Missing required parameters")
            
        if not isinstance(user_queries, list):
            raise ValueError("user_queries must be a list")
            
        # Get file from S3
        file_content = aws_service.get_file(file_id)
        
        # Get OpenAI API key from Secrets Manager
        api_key = get_openai_api_key()
        
        # Initialize OpenAI client with the API key
        client = OpenAIClient(api_key=api_key)
        
        # Process all queries
        questions = []
        for user_query in user_queries:
            # Generate a concise question using OpenAI
            questions.append(client.generate_tick_marking_question(user_query))
            
            # Analyze the document with the concise question
        analysis_result = aws_service.analyze_document(file_content, questions)
        
        # Return all results
        return {
            'statusCode': 200,
            'body': json.dumps({
                "file_id": file_id,
                "results": analysis_result
            }),
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
    except ValueError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(e)}),
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