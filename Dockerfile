FROM python:3.10-slim

WORKDIR /usr/src/app

COPY ./ ./
RUN pip install --no-cache-dir -r requirements.txt
RUN python audio_db.py

CMD ["python", "./server.py", "--port", "8080"]