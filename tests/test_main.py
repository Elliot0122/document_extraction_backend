import pytest
from fastapi.testclient import TestClient
import io
import json
from app import config

def test_upload_valid_file(test_client, mock_aws):
    """Test uploading a valid PDF file."""
    # Create a mock PDF file
    file_content = b"Mock PDF content"
    files = {
        "file": ("test.pdf", io.BytesIO(file_content), "application/pdf")
    }
    
    response = test_client.post("/upload/", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "file_id" in data
    assert "filename" in data
    assert data["filename"] == "test.pdf"

def test_upload_invalid_file_type(test_client, mock_aws):
    """Test uploading an invalid file type."""
    file_content = b"Invalid file content"
    files = {
        "file": ("test.txt", io.BytesIO(file_content), "text/plain")
    }
    
    response = test_client.post("/upload/", files=files)
    assert response.status_code == 400
    assert "File type not allowed" in response.json()["detail"]

def test_upload_large_file(test_client, mock_aws):
    """Test uploading a file that exceeds size limit."""
    large_content = b"x" * (config.MAX_FILE_SIZE + 1)
    files = {
        "file": ("large.pdf", io.BytesIO(large_content), "application/pdf")
    }
    
    response = test_client.post("/upload/", files=files)
    assert response.status_code == 400
    assert "File too large" in response.json()["detail"]

def test_query_document(test_client, mock_aws):
    """Test querying an uploaded document."""
    # First upload a file
    file_content = b"Test document content"
    files = {
        "file": ("test.pdf", io.BytesIO(file_content), "application/pdf")
    }
    
    # Upload the file
    upload_response = test_client.post("/upload/", files=files)
    assert upload_response.status_code == 200
    file_id = upload_response.json()["file_id"]
    
    # Query the document
    query_data = {
        "file_id": file_id,
        "user_query": "What is the content?"
    }
    
    response = test_client.post(
        "/query/",
        data=query_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "answer" in data
    assert "confidence" in data

def test_query_nonexistent_document(test_client, mock_aws):
    """Test querying a document that doesn't exist."""
    query_data = {
        "file_id": "nonexistent-uuid",
        "user_query": "What is the content?"
    }
    
    response = test_client.post(
        "/query/",
        data=query_data
    )
    
    assert response.status_code == 404
    assert "File not found" in response.json()["detail"] 