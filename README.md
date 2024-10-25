# wrtn-character-crawler
뤼튼 캐릭터 크롤러
---
## 1. 크롤링 수행  

- yaml파일에서 정의한 profile인 crawling 을 실행합니다. -> 크롤링 수행
- 9876 포트로 mysql이 열립니다.
```
docker compose --profile crawling up
```
---
## 2. Sqlite Export 

- DB 서비스를 실행합니다.
```
docker compose up
```

- mysql-to-sqlite3 패키지를 설치합니다. (MySQL 데이터를 SQLite로 변환하기 위한 도구)
```
pip3 install mysql-to-sqlite3
```

- MySQL DB를 SQLite로 변환합니다.
- 결과로 [out.db] 파일이 생성됩니다.
    - DB유저
        - jiwon
    - 비밀번호
        - jiwon
```
mysql2sqlite -f out.db -d wrtn_db -u DB유저 -p -P 9876
```
---
## 3. CSV 생성
- csv파일 2개 생성합니다. (sqlite 익스포트가 선행되어야 합니다.)
    - character_data.csv
    - character_category.csv
```
python3 create_csv.py
```
---
## 테스트 (로컬에서 수행됩니다. 도커 X)
- 프로젝트 의존성을 설치합니다.
- Playwright, Chromium 를 설치합니다.
- 테스트를 실행합니다.
```
poetry install
poetry run playwright install chromium
poetry run pytest
```
