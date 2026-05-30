FROM python:3.11-slim

WORKDIR /app


ENV PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir --timeout 300 --retries 5 \
    torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir --timeout 300 --retries 5 -r requirements.txt

COPY . .

EXPOSE 8000

RUN mkdir -p /app/checkpoints

CMD ["python", "main.py"]
# CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
