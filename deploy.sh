#!/bin/bash
set -e

# Load environment variables
if [ -f .env ]; then
  source .env
else
  echo "Warning: .env file not found. Using environment variables."
fi

# Force AWS region to us-west-2
export AWS_REGION=us-west-2
export AWS_DEFAULT_REGION=us-west-2
STAGE=${STAGE:-dev}
REGION=us-west-2
STACK_NAME="document-extraction-backend-${STAGE}"

# Display AWS configuration
echo "AWS Configuration:"
echo "AWS_REGION=$AWS_REGION"
echo "AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION"
echo "REGION=$REGION"
aws configure get region

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
  echo "Error: SAM CLI is not installed. Please install it."
  exit 1
fi

# Check if S3_BUCKET is set
if [ -z "$S3_BUCKET" ]; then
  echo "Error: S3_BUCKET environment variable is not set."
  echo "Please set S3_BUCKET in your .env file or environment variables."
  exit 1
fi

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Clean SAM CLI cached state for managed resources
echo "Cleaning SAM CLI cache..."
rm -rf ~/.aws-sam/managed-default

echo "Building the SAM application for ARM64..."
echo "Using AWS Region: ${REGION}"
AWS_REGION=$REGION sam build --region $REGION --use-container

# Deploy the application
echo "Deploying to ${STAGE} environment in ${REGION}..."
AWS_REGION=$REGION AWS_DEFAULT_REGION=$REGION sam deploy \
  --stack-name ${STACK_NAME} \
  --parameter-overrides \
    StageName=${STAGE} \
    S3Bucket=${S3_BUCKET} \
  --capabilities CAPABILITY_IAM \
  --region ${REGION} \
  --no-fail-on-empty-changeset \
  --s3-bucket ${S3_BUCKET} \
  --resolve-image-repos \

# Get the API endpoint URL
API_URL=$(AWS_REGION=$REGION aws cloudformation describe-stacks \
  --stack-name ${STACK_NAME} \
  --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" \
  --output text \
  --region ${REGION})

echo "Deployment completed successfully!"
echo "API Endpoint: ${API_URL}" 