FROM python:3.11-slim

# 1. Cài đặt môi trường cần thiết cho Tool (Java cho Allure)
RUN apt-get update && apt-get install -y default-jre wget unzip && rm -rf /var/lib/apt/lists/*

# 2. Cài Allure Command Line (để bảo toàn bộ công cụ báo cáo)
RUN wget https://github.com/allure-framework/allure2/releases/download/2.24.1/allure-2.24.1.tgz && \
    tar -zxvf allure-2.24.1.tgz -C /opt/ && \
    ln -s /opt/allure-2.24.1/bin/allure /usr/bin/allure

WORKDIR /app

# 3. CHỈ COPY file thư viện của Tool
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. CHỈ COPY những gì thuộc về TOOL (Tránh copy code API)
# Giả sử tool của cậu gồm các file/folder này:
COPY . .
# Tuyệt đối KHÔNG copy folder chứa code API (ví dụ: target_api/) vào đây

CMD ["python", "run_report.py"]