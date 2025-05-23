import boto3
import os
from botocore.exceptions import ClientError
from typing import List

class AWSService:
    def __init__(self):
        self.s3 = None
        self.textract = None
        self.init_clients()

    def init_clients(self):
        """Initialize or reinitialize AWS clients."""
        self.s3 = boto3.client('s3')
        self.textract = boto3.client('textract')

    def upload_file(self, file_content: bytes, file_id: str, filename: str) -> dict:
        """Upload a file to S3."""
        try:
            s3_key = f"documents/{file_id}/{filename}"

            # Upload to S3 with content type
            self.s3.put_object(
                Bucket=os.environ['S3_BUCKET'],
                Key=s3_key,
                Body=file_content,
            )
            
            # Generate pre-signed URL for immediate access
            file_url = self.s3.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': os.environ['S3_BUCKET'],
                    'Key': s3_key
                },
                ExpiresIn=86400  # URL expires in 24 hours
            )
            
            # Ensure all response values are JSON-serializable
            return {
                "message": "File uploaded successfully",
                "file_id": file_id,
                "filename": filename,
                "image_url": str(file_url)  # Ensure URL is string
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            raise Exception(f"AWS S3 error ({error_code}): {error_message}")
        except Exception as e:
            raise Exception(f"Error uploading file: {str(e)}")

    def get_file(self, file_id: str) -> bytes:
        """Get a file from S3."""
        try:
            response = self.s3.list_objects_v2(
                Bucket=os.environ['S3_BUCKET'],
                Prefix=f"documents/{file_id}/"
            )
            
            if 'Contents' not in response or not response['Contents']:
                raise FileNotFoundError("File not found")
            
            s3_key = response['Contents'][0]['Key']
            s3_response = self.s3.get_object(Bucket=os.environ['S3_BUCKET'], Key=s3_key)
            file_content = s3_response['Body'].read()
            
            return file_content
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            raise Exception(f"AWS S3 error ({error_code}): {error_message}")
        except Exception as e:
            print(f"Unexpected error in get_file: {str(e)}")
            raise Exception(f"Error retrieving file: {str(e)}")
        
    def analyze_document(self, file_content: bytes, queries: List[str]) -> List[dict]:
        """Analyze document using Textract with multiple queries.
        
        Args:
            file_content: The document content as bytes
            queries: List of queries to analyze
            
        Returns:
            List of dictionaries containing query results with format:
            [{"query": str, "answer": str, "confidence": float, "geometry": dict, "query_id": str}]
        """
        try:
            # Prepare queries for Textract
            textract_queries = [
                {'Text': query, 'Alias': f'query_{i}'}
                for i, query in enumerate(queries)
            ]
            
            # Call Textract with all queries
            response = self.textract.analyze_document(
                Document={'Bytes': file_content},
                FeatureTypes=['QUERIES'],
                QueriesConfig={
                    'Queries': textract_queries
                }
            )
            
            # Build BLOCK_MAP for easier lookup of answer sources
            block_map = {block["Id"]: block for block in response.get("Blocks", [])}
            
            # Process results
            results = []
            query_results = {}
            
            # First, collect all query results
            for block in response.get("Blocks", []):
                if block.get("BlockType") == "QUERY":
                    alias = block.get("Query", {}).get("Alias", "")
                    # Get the answer block ID from relationships, handling empty cases
                    relationships = block.get("Relationships", [])
                    answer_id = None
                    if relationships and relationships[0].get("Ids"):
                        answer_id = relationships[0]["Ids"][0]
                    
                    answer_block = block_map.get(answer_id, {}) if answer_id else {}
                    
                    query_results[alias] = {
                        "answer": answer_block.get("Text", "No answer found"),
                        "confidence": answer_block.get("Confidence", 0.0),
                        "geometry": answer_block.get("Geometry", {}).get("BoundingBox", {}),
                        "query_id": block.get("Id", "")
                    }
            
            # Then, create results for all queries, even if no answer was found
            for i, query in enumerate(queries):
                alias = f'query_{i}'
                if alias in query_results:
                    results.append({
                        "query": query,
                        "answer": query_results[alias]["answer"],
                        "confidence": query_results[alias]["confidence"],
                        "geometry": query_results[alias]["geometry"],
                        "query_id": query_results[alias]["query_id"]
                    })
                else:
                    results.append({
                        "query": query,
                        "answer": "No answer found",
                        "confidence": 0.0,
                        "geometry": {},
                        "query_id": ""
                    })
            
            return results
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            print(f"Textract error details: {error_code} - {error_message}")
            print(f"Full error response: {e.response}")
            raise Exception(f"AWS Textract error ({error_code}): {error_message}")
        except Exception as e:
            print(f"Unexpected error in analyze_document: {str(e)}")
            raise Exception(f"Error analyzing document: {str(e)}")

aws_service = AWSService()