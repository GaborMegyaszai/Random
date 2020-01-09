FROM python:3

WORKDIR /usr/src/demo
COPY . .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get update && \
    apt-get install zip
