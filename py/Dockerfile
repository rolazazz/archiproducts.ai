# BUILD the image: 
# docker build . --tag archiproducts-ai:0.3.0 --tag archiproducts-ai:latest --tag robertolazazzera/archiproducts-ai:latest
# PUSH to registy
# docker push robertolazazzera/archiproducts-ai:latest
# RUN the container:
# docker run -d -p 8000:8000 --name archiproducts-ai archiproducts-ai:latest
#
# Run/Build with Docker-Compose
# docker-compose up -d    

#FROM python:3.11-slim
FROM bitnami/pytorch:latest

USER root
RUN apt-get update && apt-get install -y git

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --upgrade -r requirements.txt
COPY . .
RUN mkdir -p /app/logs

EXPOSE 8000
# CMD ["uvicorn", "main:api", "--host", "0.0.0.0", "--port", "8000"]
CMD ["/bin/sh", "run.sh"]