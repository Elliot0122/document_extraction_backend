FROM public.ecr.aws/lambda/python:3.9-arm64

# Copy requirements file
COPY pyproject.toml .

# Install dependencies directly without installing the package
RUN pip install pip --upgrade && \
    pip install openai>=1.12.0 python-dotenv>=1.0.0 aws-lambda-powertools>=2.28.0 boto3>=1.28.65 requests>=2.31.0 fastjsonschema>=2.18.0

# Copy function code
COPY src/functions/ ${LAMBDA_TASK_ROOT}/
COPY lib/ /opt/lib/

# Set the Python path to include the /opt directory
ENV PYTHONPATH="${PYTHONPATH}:/opt"

# Create a .env file for local development if it doesn't exist
RUN touch /var/task/.env

# Set the handler
CMD [ "lambda_function.lambda_handler" ] 