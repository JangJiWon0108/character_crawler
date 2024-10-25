# https://github.com/orgs/python-poetry/discussions/1879

# Python 3.11의 경량 버전인 slim 이미지를 기반으로 새로운 이미지를 생성
FROM python:3.11-slim

# 환경변수 설정
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    PYTHONDONTWRITEBYTECODE=1

# 패키지 설치 (poetry , playwright)
# Playwright의 Chromium 브라우저와 관련된 의존성을 설치
RUN pip install poetry playwright
RUN playwright install --with-deps chromium && \
    rm -rf /var/cache/apt/archives /var/lib/apt/lists/*

# 작업 디렉토리    
WORKDIR /app

# pyproject.toml 파일을 작업 디렉토리로 복사
COPY pyproject.toml ./

# 의존성 설치
RUN poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR

#  wrtn_character_crawler의 모든 파일을 /app/wrtn_character_crawler 로 복사
COPY wrtn_character_crawler ./wrtn_character_crawler

# 엔트리 포인트 - 컨테이너가 시작될 때 실행될 기본 명령어
# wrtn_character_crawler 폴더 안 __main__.py 파일 실행
ENTRYPOINT ["poetry", "run", "python", "-u", "-m", "wrtn_character_crawler"]