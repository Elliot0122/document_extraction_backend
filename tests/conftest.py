import pytest
from fastapi.testclient import TestClient
from app.main import app, init_aws_clients
import boto3
from moto.s3 import mock_s3
from moto.textract import mock_textract
import os
from app import config

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture(autouse=True)
def mock_aws(monkeypatch):
    """Mock AWS services and initialize test environment."""
    # Set up mock AWS credentials
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_REGION", "us-west-2")
    monkeypatch.setenv("S3_BUCKET_NAME", "test-bucket")

    with mock_s3(), mock_textract():
        # Create mock S3 bucket
        s3_client = boto3.client(
            "s3",
            aws_access_key_id="testing",
            aws_secret_access_key="testing",
            region_name="us-west-2"
        )
        
        # Create the test bucket
        s3_client.create_bucket(
            Bucket="test-bucket",
            CreateBucketConfiguration={"LocationConstraint": "us-west-2"}
        )
        
        # Reinitialize the main app's AWS clients with mock credentials
        init_aws_clients()
        
        yield 