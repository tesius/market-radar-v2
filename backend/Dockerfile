# 1. 베이스 이미지: 파이썬 3.11 슬림 버전 (가볍고 빠름)
FROM python:3.13-slim-bookworm

# 2. 작업 디렉토리 설정
WORKDIR /app

# 2-1. 타임존 설정 (Asia/Seoul)
ENV TZ=Asia/Seoul
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 3. 의존성 파일 먼저 복사 (캐싱 효율을 위해 소스보다 먼저)
COPY requirements.txt .

# 4. 라이브러리 설치
# --no-cache-dir: 설치 후 임시 파일을 지워서 용량을 줄임
RUN pip install --no-cache-dir -r requirements.txt

# 5. 나머지 소스 코드 전체 복사
COPY . .

# 6. 포트 노출 (Fly.io 기본값 8080)
EXPOSE 8080

# 7. 실행 명령어 (가장 안전한 python -m 방식)
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]