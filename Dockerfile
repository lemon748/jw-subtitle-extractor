# 1. 이미 브라우저와 파이썬이 다 설치된 공식 이미지를 가져옵니다.
FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

# 2. 작업 폴더 설정
WORKDIR /app

# 3. 파일 복사
COPY . /app

# 4. 파이썬 라이브러리 설치 (flask 등)
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# 5. 브라우저 설치 (시스템 의존성은 이미 이미지에 포함됨)
RUN playwright install chromium

# 6. 서버 실행 명령어 (Render가 포트를 알아서 연결해줍니다)
CMD gunicorn app:app -b 0.0.0.0:10000
