import boto3
from botocore.exceptions import ClientError
from .. import config

class AWSService:
    def __init__(self):
        self.s3 = None
        self.textract = None
        self.init_clients()

    def init_clients(self):
        """Initialize or reinitialize AWS clients."""
        self.s3 = boto3.client('s3',
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
            region_name=config.AWS_REGION
        )
        self.textract = boto3.client('textract',
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
            region_name=config.AWS_REGION
        )

    def upload_file(self, file_content: bytes, file_id: str, filename: str) -> dict:
        """Upload a file to S3."""
        s3_key = f"documents/{file_id}/{filename}"
        self.s3.put_object(
            Bucket=config.S3_BUCKET_NAME,
            Key=s3_key,
            Body=file_content
        )
        return {
            "message": "File uploaded successfully",
            "file_id": file_id,
            "filename": filename
        }

    def get_file(self, file_id: str) -> bytes:
        """Get a file from S3."""
        response = self.s3.list_objects_v2(
            Bucket=config.S3_BUCKET_NAME,
            Prefix=f"documents/{file_id}/"
        )
        
        if 'Contents' not in response or not response['Contents']:
            raise FileNotFoundError("File not found")
        
        s3_key = response['Contents'][0]['Key']
        s3_response = self.s3.get_object(Bucket=config.S3_BUCKET_NAME, Key=s3_key)
        return s3_response['Body'].read()

    def analyze_document(self, file_content: bytes, query: str) -> dict:
        """Analyze document using Textract."""
        response = self.textract.analyze_document(
            Document={'Bytes': file_content},
            FeatureTypes=['QUERIES'],
            QueriesConfig={
                'Queries': [
                    {'Text': query, 'Alias': 'user_query'}
                ]
            }
        )
        
        for block in response.get("Blocks", []):
            if block.get("BlockType") == "QUERY_RESULT":
                return {
                    "query": query,
                    "answer": block["Text"],
                    "confidence": block.get("Confidence", 0)
                }
        
        return {
            "query": query,
            "answer": "No relevant answer found.",
            "confidence": 0
        }

    def cleanup_old_files(self, hours: int = 24):
        """Remove files older than specified hours from S3 bucket."""
        try:
            from datetime import datetime, timedelta
            cutoff_time = datetime.now() - timedelta(hours=hours)

            paginator = self.s3.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=config.S3_BUCKET_NAME, Prefix='documents/'):
                if 'Contents' not in page:
                    continue

                for obj in page['Contents']:
                    last_modified = obj['LastModified'].replace(tzinfo=None)
                    
                    if last_modified < cutoff_time:
                        try:
                            self.s3.delete_object(
                                Bucket=config.S3_BUCKET_NAME,
                                Key=obj['Key']
                            )
                            print(f"Deleted: {obj['Key']}")
                        except ClientError as e:
                            print(f"Error deleting {obj['Key']}: {str(e)}")

        except Exception as e:
            print(f"Error during cleanup: {str(e)}") 