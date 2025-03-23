import boto3
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
import time
from . import config

def cleanup_old_files():
    """Remove files older than 24 hours from S3 bucket."""
    try:
        # Initialize S3 client
        s3 = boto3.client('s3',
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
            region_name=config.AWS_REGION
        )

        # Calculate cutoff time (24 hours ago)
        cutoff_time = datetime.now() - timedelta(hours=24)

        # List all objects in the documents directory
        paginator = s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=config.S3_BUCKET_NAME, Prefix='documents/'):
            if 'Contents' not in page:
                continue

            for obj in page['Contents']:
                # Get the last modified time of the object
                last_modified = obj['LastModified'].replace(tzinfo=None)
                
                # If the file is older than 24 hours
                if last_modified < cutoff_time:
                    try:
                        # Delete the object
                        s3.delete_object(
                            Bucket=config.S3_BUCKET_NAME,
                            Key=obj['Key']
                        )
                        print(f"Deleted: {obj['Key']}")
                    except ClientError as e:
                        print(f"Error deleting {obj['Key']}: {str(e)}")

    except Exception as e:
        print(f"Error during cleanup: {str(e)}")

def run_continuous_cleanup():
    """Run cleanup continuously with 24-hour intervals."""
    print("Starting continuous cleanup service...")
    while True:
        print(f"Running cleanup at {datetime.now()}")
        cleanup_old_files()
        print("Cleanup completed. Sleeping for 24 hours...")
        time.sleep(24 * 60 * 60)  # Sleep for 24 hours

if __name__ == "__main__":
    run_continuous_cleanup() 