FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml main.py ./
COPY dependencies dependencies
COPY orchestrator orchestrator
COPY services services
COPY slash_commands slash_commands

RUN pip install --no-cache-dir .

VOLUME ["/app/config"]

EXPOSE 8787 8788

CMD ["python", "main.py"]
