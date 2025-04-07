FROM public.ecr.aws/lambda/python:3.9-arm64

# Install uv
RUN pip install pip --upgrade && \
    pip install uv

# Copy project metadata and generate requirements file
COPY pyproject.toml ./
RUN uv pip compile pyproject.toml -o requirements.txt

# Install dependencies from generated requirements
RUN uv pip install --system -r requirements.txt

# Copy function code
COPY src/functions/ ${LAMBDA_TASK_ROOT}/
COPY lib/ /opt/lib/

# Set the Python path to include the /opt directory
ENV PYTHONPATH="${PYTHONPATH}:/opt"

# Create a .env file for local development if it doesn't exist
RUN touch /var/task/.env

# Set the handler
CMD [ "lambda_function.lambda_handler" ] 