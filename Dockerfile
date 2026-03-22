FROM python:3.10-slim

# 安装 OCR + 时区
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tzdata

ENV TZ=Asia/Shanghai

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]