import os
import sys
from pathlib import Path

def setup_aws_ssl():
    """Help set up AWS SSL certificates."""
    cert_file = "aws-cert.pem"
    key_file = "aws-key.pem"
    
    print("AWS SSL Certificate Setup")
    print("------------------------")
    print("\n1. Go to AWS Certificate Manager (ACM)")
    print("2. Select your certificate")
    print("3. Click 'Export'")
    print("4. Save the certificate and private key files")
    print("\nPlace the files in the project root:")
    print(f"- Certificate file: {cert_file}")
    print(f"- Private key file: {key_file}")
    
    # Check if files exist
    cert_path = Path(cert_file)
    key_path = Path(key_file)
    
    if cert_path.exists() and key_path.exists():
        print("\n✓ Certificate files found!")
        print("\nSetting secure permissions...")
        try:
            os.chmod(cert_path, 0o644)  # Readable by all
            os.chmod(key_path, 0o600)   # Readable only by owner
            print("✓ Permissions set successfully!")
        except Exception as e:
            print(f"Warning: Could not set permissions: {e}")
    else:
        print("\n✗ Certificate files not found!")
        print("Please download and place the files as described above.")
        sys.exit(1)

if __name__ == "__main__":
    setup_aws_ssl() 