FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Cài các công cụ cần thiết và Docker CLI
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        gnupg \
        lsb-release \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | \
        gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
        https://download.docker.com/linux/debian $(lsb_release -cs) stable" \
        > /etc/apt/sources.list.d/docker.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends docker-ce-cli && \
    apt-get purge -y gnupg lsb-release && \
    apt-get autoremove -y && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Tạo user không phải root
RUN groupadd -g 998 docker && \
    adduser --disabled-password --gecos '' appuser && \
    usermod -aG docker appuser

# Sao chép mã nguồn vào container
WORKDIR /app
COPY . /app

# Cài đặt dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    chown -R appuser:appuser /app

# Chạy bằng user appuser
USER appuser

# Thiết lập môi trường Flask
ENV FLASK_APP=app.py \
    FLASK_RUN_HOST=0.0.0.0 \
    FLASK_RUN_PORT=8000 \
    FLASK_ENV=production

EXPOSE 8000

# Khởi động Flask
CMD ["flask", "run"]
