import os
from dotenv import load_dotenv

load_dotenv()

# AWS Configuration
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', 'testing')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', 'testing')
AWS_REGION = os.getenv('AWS_REGION', 'us-west-2')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'test-bucket')

# File Upload Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_FILE_TYPES = ['.pdf', '.png', '.jpg', '.jpeg'] 