# create_csv.py
# 요약 : out.db 파일에 연결하여 캐릭터 데이터 테이블, 캐릭터 카테고리 테이블 조회 후, 각 10개씩을 추출해 CSV 파일로 저장

import sqlite3
import csv

# 결과로 나온 sqlite 파일인 out.db 연결
conn = sqlite3.connect("out.db")

# 캐릭터 데이터 정보 테이블 컬럼 정의
char_data_columns = [
    "id",                   # 1부터 증가하는 ID (기본키)
    "wrtn_id",              # 뤼튼 고유 ID
    "name",                 # 캐릭터 이름
    "description",          # 설명
    "profile_url",          # 프로필 이미지 URL
    "author",               # 제작자
    "initial_message",      # 첫 메시지
]

# 상위 10개를 SELECT 하는 쿼리문
#  char_data_columns 리스트 요소들을 , 로 연결
char_data_query = f"SELECT {', '.join(char_data_columns)} FROM CharacterData LIMIT 10;"

# excute를 통해 쿼리문을 실행하고, 결과를 fetchall() 메서드를 이용해 반환
# char_data 에 결과 저장
char_data = conn.execute(char_data_query).fetchall()

# 카테고리 테이블 컬럼 정의
category_columns = [
    "id",                 # 1부터 증가하는 ID
    "character_id",       # 왜래키 (캐릭터 정보 테이블의 ID를 참조함)
    "name",               # 카테고리 (사이트보면 category의 name에 카테고리가 있음)
]

# 마찬가지로 상위 10개를 추출하는 쿼리문 및 결과를 반환해 category 에 저장
category_query = f"SELECT {', '.join(category_columns)} FROM CharacterCategory LIMIT 10;"
category = conn.execute(category_query).fetchall()

# 아래부터는 csv 파일을 2개 생성하는 부분

# 캐릭터 데이터 정보 csv 파일로 저장
# w는 쓰기모드
# newline='' 로 해 줄바꿈을 적용하지 않음 (하지않으면 각 행마다 줄바꿈이 적용됨)
# 인코딩 방식지정
with open("character_data.csv", "w", newline='', encoding="euckr") as f:
    writer = csv.writer(f)                  # csv 작성기 객체 생성
    writer.writerow(char_data_columns)      # 컬럼을 char_data_columns 로 설정
    writer.writerows(char_data)             # char_data를 row로 작성

with open("character_category.csv", "w", newline='', encoding=" euckr") as f:
    writer = csv.writer(f)                # csv 작성기 객체 생성
    writer.writerow(category_columns)    # 컬럼을 category_columns 로 설정
    writer.writerows(category)           # category를 row로 작성


# 데이터베이스 연결 종료
conn.close()
