FROM python:3.10-slim
WORKDIR /app
COPY app.py .
RUN pip install flask docker requests
CMD ["python", "app.py"]
