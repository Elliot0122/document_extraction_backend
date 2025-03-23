import os
from pathlib import Path

# SSL Configuration
SSL_CERT_FILE = os.getenv("SSL_CERT_FILE", "aws-cert.pem")
SSL_KEY_FILE = os.getenv("SSL_KEY_FILE", "aws-key.pem")
SSL_CERT_PATH = Path(__file__).parent.parent.parent / SSL_CERT_FILE
SSL_KEY_PATH = Path(__file__).parent.parent.parent / SSL_KEY_FILE

# Verify SSL files exist
if not SSL_CERT_PATH.exists() or not SSL_KEY_PATH.exists():
    raise FileNotFoundError(
        "SSL certificate or key file not found. "
        f"Please ensure {SSL_CERT_FILE} and {SSL_KEY_FILE} exist in the project root. "
        "You can download these from AWS Certificate Manager."
    )

# Set proper permissions for security
def set_secure_permissions():
    """Set secure permissions for SSL files."""
    try:
        os.chmod(SSL_CERT_PATH, 0o644)  # Readable by all
        os.chmod(SSL_KEY_PATH, 0o600)   # Readable only by owner
    except Exception as e:
        print(f"Warning: Could not set SSL file permissions: {e}")

# Set permissions when module is imported
set_secure_permissions() 