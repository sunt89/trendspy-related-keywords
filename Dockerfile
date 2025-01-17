FROM python:3.13.1
WORKDIR /app

COPY . ./
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "trends_monitor.py"]