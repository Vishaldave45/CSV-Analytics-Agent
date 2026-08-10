FROM python:3.10-slim

# Prevent bytecode & buffer output
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create non-root unprivileged sandbox user (UID/GID 1000)
RUN groupadd -g 1000 sandboxuser && \
    useradd -u 1000 -g sandboxuser -m sandboxuser

WORKDIR /workspace
RUN chown -R sandboxuser:sandboxuser /workspace

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

USER sandboxuser:sandboxuser

CMD ["python3"]
