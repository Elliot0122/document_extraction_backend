from lib.aws_service import aws_service
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

def handle_upload(event):
    """Handle file upload."""
    try:
        # Parse the multipart form data
        body = event['body']
        if event.get('isBase64Encoded', False):
            body = base64.b64decode(body)
        else:
            body = body.encode('utf-8')
            
        # Extract file content and metadata
        content_type = event['headers'].get('content-type', '')
        if 'boundary=' not in content_type:
            raise ValueError("Invalid content type: missing boundary")
            
        boundary = content_type.split('boundary=')[1]
        parts = body.split(b'--' + boundary.encode())
        
        file_content = None
        filename = None
        
        for part in parts:
            if b'Content-Disposition: form-data; name="file"' in part:
                headers, content = part.split(b'\r\n\r\n', 1)
                file_content = content.rstrip(b'\r\n')
                
                # Extract filename from headers
                filename_header = [h for h in headers.split(b'\r\n') if b'filename=' in h][0]
                filename = filename_header.split(b'filename=')[1].strip(b'"').decode()
                break
        
        if not file_content or not filename:
            raise ValueError("No file found in request")
            
        # Validate file size and type
        file_size = len(file_content)
        if file_size > 10 * 1024 * 1024:  # 10MB
            raise ValueError("File too large")
            
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in ['.jpg', '.jpeg', '.png', '.pdf']:
            raise ValueError("File type not allowed")
            
        # Generate file ID and upload
        file_id = str(uuid.uuid4())
        response = aws_service.upload_file(file_content, file_id, filename)
        
        return {
            'statusCode': 200,
            'body': json.dumps(response),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
        
    except Exception as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(e)}),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
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