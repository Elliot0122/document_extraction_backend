import threading
import time
from datetime import datetime
from .aws_service import AWSService

class CleanupService:
    def __init__(self, aws_service: AWSService, cleanup_interval_hours: int = 24):
        self.aws_service = aws_service
        self.cleanup_interval_hours = cleanup_interval_hours
        self.thread = None
        self.is_running = False

    def _run_cleanup_service(self):
        """Run cleanup service in background."""
        print("Starting cleanup service...")
        while self.is_running:
            print(f"Running cleanup at {datetime.now()}")
            self.aws_service.cleanup_old_files(self.cleanup_interval_hours)
            print(f"Cleanup completed. Sleeping for {self.cleanup_interval_hours} hours...")
            time.sleep(self.cleanup_interval_hours * 60 * 60) 