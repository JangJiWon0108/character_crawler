# database.py
# 요약 : 데이터베이스 작업을 처리 (db연결, 데이터 추가, 데이터 조회)

from dataclasses import dataclass
import json
import time
import pymysql # MySQL 데이터베이스와 연결하기 위한 pymysql 모듈
from pymysql.cursors import Cursor
from typing import Optional

from wrtn_character_crawler.models import Character  # Character 클래스 가져옴

@dataclass
class DBConfig:    # 데이터베이스 구성 정보를 저장하는 데이터 클래스를 정의
    host: str      # 호스트 주소 
    user: str      # 유저 이름
    password: str  # 비밀번호
    database: str  # DB 이름

# 데이터베이스 초기화 쿼리
# 2개 테이블 생성함 (캐릭터 데이터, 캐릭터 카테고리)

# 캐릭터 데이터 테이블
#  - 자동 증가하는 기본키 ID
#  - 뤼튼 고유 ID
#  - 캐릭터명
#  - 캐릭터 설명
#  - 프로필 이미지 URL
#  - 프로필 이미지 바이너리 형식
#  - 첫 메시지

# 카테고리 테이블
#  - 자동 증가하는 기본키 ID
#  - 캐릭터 ID 
#  - 카테고리 (category의 name에 카테고리가 있어서 name으로 지정ㅎ암)
#  - 왜래키 제약조건
TABLE_INIT = (
    """
    CREATE TABLE IF NOT EXISTS CharacterData(
        id INT AUTO_INCREMENT PRIMARY KEY,
        wrtn_id VARCHAR(255) NOT NULL UNIQUE,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        profile_url TEXT,
        profile_image MEDIUMBLOB,
        author VARCHAR(255),
        initial_message TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS CharacterCategory (
        id INT AUTO_INCREMENT PRIMARY KEY,
        character_id INT,
        name VARCHAR(255),
        FOREIGN KEY (character_id) REFERENCES CharacterData(id)
    );
    """,
)

# 데이터베이스 작업을 처리하는 Database 클래스를 정의
class Database:

    # 클래스의 초기화 메서드
    def __init__(self, config: DBConfig):
        while True: # 연결성공할때까지 무한루프
            try:
                # DB연결
                self.conn = pymysql.connect(
                    host=config.host,          # 데이터베이스 호스트
                    user=config.user,          # 유저 이름
                    password=config.password,  # 비밀번호
                    database=config.database,  # 데이터베이스 이름
                    charset="utf8mb4",         # 인코딩 방식
                )

                print("db connected")   # 연결 성공 메시지
                break                   # 무한루프 탈출

            # 예외처리
            except:
                print("db reconnecting..")  # 연결되지않으면 계속시도
                time.sleep(2)

        self.cursor: Cursor = self.conn.cursor() # DB작업을 위한 커서 생성

        # 데이터베이스 초기화 쿼리 실행
        for script in TABLE_INIT:
            self.cursor.execute(script) # 실행
            self.conn.commit()          # 커밋

    # 캐릭터 추가 메서드
    def add_character(self, character: Character) -> int:
        try:
            # 캐릭터 데이터 테이블에 데이터 INSERT함
            self.cursor.execute(
                """
                INSERT INTO CharacterData (wrtn_id, name, description, profile_url, profile_image, author, initial_message)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    character.wrtn_id,           # 뤼튼 고유 ID
                    character.name,              # 캐릭터명 
                    character.description,       # 설명
                    character.profile_url,       # 프로필 이미지 URL
                    character.profile_image,     # 프로필 이미지 바이너리 형식
                    character.author,            # 작성자(제작자)
                    character.initial_message,   # 첫 메시지
                ),
            )

            # INSERT한 데이터 레코드의 기본키를 가져옴 (자동증가하는 기본키)
            # 이것을 이용해 캐릭터 카테고리 테이블에 데이터를 추가함
            character_id = self.cursor.lastrowid

            # 캐릭터 카테고리 테이블에 INSERT 함
            # 위에서 가져온 id 랑 카테고리 데이터 추가
            for category in character.categories:
                self.cursor.execute(
                    """
                    INSERT INTO CharacterCategory (character_id, name)
                    VALUES (%s, %s)
                    """,
                    (character_id, category),
                )

            self.conn.commit()   # 커밋함

            return character_id  # 추가된 캐릭터의 ID 를 반환 (1씩 증가하는 기본키)
        
        # 예외처리
        except Exception as e:
            self.conn.rollback()  # 오류 발생 시 롤백
            raise e

    # 캐릭터 조회 메서드
    def get_character(self, wrtn_id: str) -> Optional[Character]:

        # select 문을 사용해 CharacterData 테이블에서 해당되는 id로 조회함
        self.cursor.execute(
            """
            SELECT id, wrtn_id, name, description, profile_url, profile_image, author, initial_message
            FROM Character WHERE wrtn_id = %s
            """,
            (wrtn_id,),
        )

        # 한 행을 가져와 없다면 None 반환
        row = self.cursor.fetchone()
        if not row:
            return None

        # select 문을 사용해 CharacterCategory 테이블에서 해당되는 id로 조회함 
        self.cursor.execute(
            """
            SELECT name
            FROM CharacterCategory WHERE character_id = %s
            """,
            (row[0],),
        )

        # 쿼리 결과 가져옴 : self.cursor.fetchall() - 주어진 id에 해당되는 모든 카테고리 이름을 포함하는 행들을 리스트로
        # 튜플로 반환
        categories = list(sum(self.cursor.fetchall(), tuple()))

        # 반환
        # 주어진 id에 해당되는 캐릭터의 모든 카테고리 정보를 추가해 반환
        return Character(
            wrtn_id=row[1],
            name=row[2],
            description=row[3],
            profile_url=row[4],
            profile_image=row[5],
            author=row[6],
            initial_message=row[7],
            categories=categories,
        )
    
    # 데이터베이스 연결 종료 메서드
    def close(self):
        self.conn.close()
