# create_csv_total.py
# 요약 : out.db 파일에 연결하여 캐릭터 데이터 테이블, 캐릭터 카테고리 테이블 조회 후, CSV 파일로 저장

import sqlite3
import csv

conn = sqlite3.connect("out.db")

char_data_columns = [
    "id",
    "wrtn_id",
    "name",
    "description",
    "profile_url",
    "author",
    "initial_message",
]
char_data_query = f"SELECT {', '.join(char_data_columns)} FROM CharacterData;"
char_data = conn.execute(char_data_query).fetchall()

category_columns = [
    "id",
    "character_id",
    "name",
]
category_query = f"SELECT {', '.join(category_columns)} FROM CharacterCategory;"
category = conn.execute(category_query).fetchall()

with open("character_data.csv_total.csv", "w", newline='', encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(char_data_columns)
    writer.writerows(char_data)

with open("character_category.csv_total.csv", "w", newline='', encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(category_columns)
    writer.writerows(category)

conn.close()
