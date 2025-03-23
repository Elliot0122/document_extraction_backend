import uvicorn
from app.config.ssl_config import SSL_CERT_PATH, SSL_KEY_PATH
import os

if __name__ == "__main__":
    # Check if running with sudo (needed for port 443)
    if os.geteuid() != 0:
        print("Warning: This script needs to be run with sudo to use port 443")
        print("Please run: sudo uv run -m run_https")
        exit(1)

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=443,  # Standard HTTPS port
        ssl_keyfile=str(SSL_KEY_PATH),
        ssl_certfile=str(SSL_CERT_PATH),
        reload=True
    ) 