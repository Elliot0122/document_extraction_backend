from setuptools import setup, find_packages

setup(
    name="document_extraction_backend",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.104.1",
        "python-multipart==0.0.6",
        "boto3==1.29.0",
        "python-dotenv==1.0.0",
        "uvicorn==0.24.0",
        "pydantic==2.4.2",
    ],
) 