# test_crawler.py 
# 요약 : 크롤링 테스트 파일 
# Crawler 클래스가 API로부터 올바르게 데이터를 크롤링하는지 검증하는 테스트 파일

import asyncio
from urllib.parse import urlparse
import pytest
from playwright.async_api import async_playwright, Response

from wrtn_character_crawler.crawler import Crawler     # 크롤러 클래스
from wrtn_character_crawler.models import Character    # 데이터 클래스
from typing import List, Optional
from jsonschema import validate  # JSON 데이터 유효성 검증에 사용

# 테스트 목적인 DB 클래스
class MockedDB:

    # 생성자
    def __init__(self):
        self.data: List[Character] = []  # 빈리스트 저장

    # 데이터 추가 메서드
    # 추가된 데이터의 인덱스를 반환
    def add_character(self, character: Character) -> int:
        self.data.append(character)   # 리스트에 데이터 추가
        return len(self.data) - 1     # 추가된 데이터의 인덱스를 반환

    # 데이터 조회 메서드
    # wrtn_id 값을 기준으로 data 리스트에서 데이터를 조회함
    # 일치하는 데이터가 있으면 그 Character 객체 반환
    # 없으면 None 반환 (next함수의 기본값이 None)
    def get_character(self, wrtn_id: str) -> Optional[Character]:
        return next(filter(lambda v: v.wrtn_id == wrtn_id, self.data))

    # close 메서드
    def close(self):
        pass
# Crawler 클래스의 크롤링 기능이 올바르게 작동하는지 테스트하는 함수
@pytest.mark.asyncio
async def test_crawler():
    
    # 크롬 브라우저 실행
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()   # 크롬 브라우저 실행
        context = await browser.new_context()          # context 생성

        try:
            
            db = MockedDB()        # db 객체 생성
            crawler = Crawler(db)  # 크롤러 객체 생성

            # API 모킹
            await context.route(
                "*/**/be/characters?*",
                lambda route: route.fulfill(
                    json={
                        "result": "SUCCESS",
                        "data": {
                            "characters": [
                                {
                                    "_id": "00aabbccddeeff",
                                    "name": "테스트 캐릭터1",
                                    "description": "테스트테스트1",
                                    "profileImage": {
                                        "origin": "https://www.gstatic.com/webp/gallery3/1.sm.png"
                                    },
                                    "creator": {"nickname": "admin"},
                                    "initialMessages": ["안녕하세요"],
                                    "categories": [{"name": "카테고리1"}],
                                },
                                {
                                    "_id": "11aabbccddeeff",
                                    "name": "테스트 캐릭터2",
                                    "description": "테스트테스트2",
                                    "profileImage": {
                                        "origin": "https://www.gstatic.com/webp/gallery3/1.sm.png"
                                    },
                                    "creator": {"nickname": "admin"},
                                    "initialMessages": ["안녕하세요"],
                                    "categories": [{"name": "카테고리2"}],
                                },
                            ],
                            "nextCursor": None,
                        },
                    }
                ),
            )

            # 새로운 페이지 열기
            page = await context.new_page()

            # crawl 메서드로 페이지를 크롤링
            await crawler.crawl(page)

            # get_character 를 이용해 데이터를 가져와 속성값을 검증
            # assert 구문은 실제 값이 예상 값과 동일한지 확인
            # 모든 assert가 성공하면 크롤러가 정상적으로 데이터를 저장했다는 것
            character = db.get_character("00aabbccddeeff")
            assert character is not None
            assert character.name == "테스트 캐릭터1"
            assert character.description == "테스트테스트1"
            assert character.initial_message == "안녕하세요"
            assert character.categories == ["카테고리1"]
            assert character.profile_image is not None
            assert (
                character.profile_url
                == "https://www.gstatic.com/webp/gallery3/1.sm.png"
            )

            character = db.get_character("11aabbccddeeff")
            assert character is not None
            assert character.name == "테스트 캐릭터2"
            assert character.description == "테스트테스트2"
            assert character.initial_message == "안녕하세요"
            assert character.categories == ["카테고리2"]
            assert character.profile_image is not None
            assert (
                character.profile_url
                == "https://www.gstatic.com/webp/gallery3/1.sm.png"
            )

        # finally 는 에러발생 상관없이 반드시 실행
        finally:
            await context.close()  # context 닫기
            await browser.close()  # 브라우저 닫기
            db.close()             # db닫기


# JSON 응답을 검증하는 데 사용되는 스키마(API_RESP_SCHEMA)
# JSON 스키마 형식으로 정의되어 있으며, 응답 데이터가 주어진 구조를 정확히 따르고 있는지 확인하는 데 사용
API_RESP_SCHEMA = {
    "type": "object",
    "properties": {
        "result": {"type": "string"},
        "data": {
            "type": "object",
            "properties": {
                "characters": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "_id": {"type": "string"},
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "profileImage": {
                                "type": "object",
                                "properties": {
                                    "origin": {"type": "string"},
                                },
                                "required": ["origin"],
                            },
                            "creator": {
                                "type": "object",
                                "properties": {
                                    "nickname": {"type": "string"},
                                },
                                "required": ["nickname"],
                            },
                            "initialMessages": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "categories": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                    },
                                    "required": ["name"],
                                },
                            },
                        },
                        "required": [
                            "_id",
                            "name",
                            "description",
                            "profileImage",
                            "creator",
                            "initialMessages",
                            "categories",
                        ],
                    },
                },
                "nextCursor": {"type": ["string", "null"]},
            },
            "required": ["characters", "nextCursor"],
        },
    },
    "required": ["result", "data"],
}