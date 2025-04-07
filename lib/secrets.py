import json
import os
from typing import Dict, cast

import boto3
from botocore.exceptions import ClientError

# Cache for secrets to minimize API calls
_secret_cache: Dict[str, str] = {}


def get_secret(secret_name: str, use_cache: bool = True) -> str:
    """
    Retrieve a secret from AWS Secrets Manager.

    Args:
        secret_name: The name or ARN of the secret to retrieve
        use_cache: Whether to use cached value if available

    Returns:
        The secret string value

    Raises:
        Exception: If the secret cannot be retrieved
    """
    # Check if we have a cached version
    if use_cache and secret_name in _secret_cache:
        return _secret_cache[secret_name]

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager")

    try:
        # Get the secret value
        response = client.get_secret_value(SecretId=secret_name)

        # Parse and return the secret
        if "SecretString" in response:
            secret = response["SecretString"]

            # If the secret is a JSON string, parse it
            try:
                secret_dict = json.loads(secret)
                # If it's a key-value pair, return the value
                if isinstance(secret_dict, dict) and len(secret_dict) == 1:
                    secret = list(secret_dict.values())[0]
            except json.JSONDecodeError:
                # If it's not JSON, just return the raw string
                pass

            # Cache the secret
            _secret_cache[secret_name] = secret
            return cast(str, secret)
        else:
            raise ValueError("Secret value is binary and not supported")

    except ClientError as e:
        # In development, fall back to environment variables
        if os.environ.get("ENVIRONMENT") == "development" or "SAM_LOCAL" in os.environ:
            # Convert secret name format to env var format (e.g., dev/openai/api-key -> OPENAI_API_KEY)
            env_var = secret_name.split("/")[-1].replace("-", "_").upper()
            env_value = os.environ.get(env_var)
            if env_value:
                return cast(str, env_value)

        raise


def get_openai_api_key() -> str:
    """
    Get the OpenAI API key from Secrets Manager or environment variables.

    Returns:
        The OpenAI API key
    """
    # Check if we're running locally with SAM
    is_local = "SAM_LOCAL" in os.environ

    # If running locally, prefer direct environment variable
    if is_local:
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            return cast(str, api_key)

    # Try to get from secret manager
    secret_name = os.environ.get("OPENAI_API_KEY_SECRET_NAME")
    if secret_name:
        try:
            return get_secret(secret_name)
        except Exception as e:
            if is_local:
                # Don't raise an error if running locally
                pass
            else:
                # Only raise in production
                raise

    # Fall back to environment variables
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not found in Secrets Manager or environment variables")

    return cast(str, api_key)
