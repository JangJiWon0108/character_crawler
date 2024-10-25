# crawler.py
# 요약 : 뤼튼 사이트에서 캐릭터 크롤링 작업 수행

import asyncio
from typing import Optional
from playwright.async_api import Page, Response
import aiohttp
from urllib.parse import urlparse

from wrtn_character_crawler.database import Database   # database 에서 Database 클래스를 가져옴
from wrtn_character_crawler.models import Character    # models 에서 Character 클래스를 가져옴

# 뤼튼 캐릭터 페이지의 스크롤을 내리기 위한 JS 코드
SCROLL_DOWN_SCRIPT = """
const ele = document.querySelector("#character-explore-scroll")
ele.scrollTo({
    top: ele.scrollHeight,
});
"""

# 크롤러 클래스 정의
class Crawler:
    SCROLL_DELAY = 1  # 스크롤 딜레이 1초로 설정

    def __init__(self, db: Database):
        self.done = False      # 크롤링 완료를 나탄태는 플래그 변수
        self.db = db           # 데이터베이스 객체 저장

    # 캐릭터 프로필 이미지 URL을 바이트 형식으로 리턴하는 메서드
    # 매개변수는 str형식의 url
    # 반환값은 바이트 형식  
    @staticmethod
    async def fetch_profile_image(url: str) -> Optional[bytes]:

        # url 이 없으면 None 반환
        if not url:
            return None

        # HTTP 세션 생성
        async with aiohttp.ClientSession() as session:

            # 시도
            try:
                # 이미지 URL 요청
                async with session.get(url) as response:
                    response.raise_for_status()    # 응답 상태 확인
                    return await response.read()   # 바이트 형태로 반환
                
            # 오류 발생 시 None 반환
            except Exception as e:
                print(f"이미지 다운로드 오류 {e}")
                return None
    
    # dict (json) 형식으로 받은 캐릭터데이터를 파싱해 Character 객체로 변환하는 메서드
    # 매개변수는 dict 형식의 캐릭터 데이터
    # 반환은 Character 객체
    def parse_character(self, data: dict) -> Character:

        # 속성에서 캐릭터의 프로필 이미지의 URL를 안전하게 추출하는 코드
        # profileImage 의 origin 에 정의되어 있음
        # (필드가 없거나 비어 있을 수 있는 상황을 처리하여 예외 발생을 방지)
        # profileImage를 가져옴(없다면 빈 딕셔너리)
        # 그리고 그 안에서 origin 가져옴 (없다면 None)
        profile_url = (data.get("profileImage") or {}).get("origin") or None

        # Character 객체를 반환
        return Character(
            wrtn_id=data["_id"],                                      # 고유 id
            name=data["name"],                                        # 캐릭터 이름
            description=data["description"],                          # 캐릭터 설명
            profile_url=profile_url,                                  # 위에서 추출한 이미지 url
            profile_image=None,                                       # 이미지 바이트 형식은 나중에 채울예정이므로 일단 None 
            author=data["creator"]["nickname"],                       # 캐릭터 제작자
            initial_message=data["initialMessages"][0],               # 첫 메시지
            categories=[cat["name"] for cat in data["categories"]],   # 카테고리 (categories 에서 name 이 카테고리임)
        )
    
    # response 객체를 받아 처리하는 메서드 정의
    async def handle_response(self, response: Response):

        # 만약 크롤링이 완료되었다면(slef.done 이 True 라면) 종료
        if self.done:
            return

        # url 파싱
        # response url 을 보면 https://api.wrtn.ai/be/characters?limit=24&cursor= .... 형태임
        # 따라서 해당 url이 아니라면 종료함
        url = urlparse(response.url)
        if url.hostname != "api.wrtn.ai" or url.path != "/be/characters":
            return

        # 응답형식을 json 형식으로 반환해 저장함
        # (API 응답은 JSON 형식으로 되어 있기 때문에 데이터를 쉽게 다룰 수 있도록 변환)
        resp: dict = await response.json()

        # json의 result 에는 응답 성공 여부 정보가 저장
        # 그래서 만약 SUCCESS 가 아니라면 오류를 출력하고, 플래그 변수 done을 true로 바꾼 뒤 종료
        if resp.get("result") != "SUCCESS":
            print("응답 오류", resp)
            self.done = True
            return

        # 응답이 성공이라면 아래 실행함
        # 응답의 data에서 characters에 각 캐릭터 정보가 담겨져 있음
        # 따라서 for문으로 순회하면서 각 캐릭터 정보를 가져옴
        # 위에서 정의한 parse_character 메서드 이용해서 파싱함
        for char_data in resp["data"]["characters"]:
            character = self.parse_character(char_data)

            # 캐릭터 url 이 있다면 수행
            # 위에서 정의한 fetch_profile_image 메서드를 이용 (이미지url 을 바이트 형식으로 반환하는 메서드)
            # 바이트 형식으로 반환해 위에서 None으로 채웠던 속성을 바이트 값으로 채움 
            if character.profile_url:
                character.profile_image = await self.fetch_profile_image(
                    character.profile_url
                )

            # database 클래스의 add_character() 메서드를 이용해 데이터베이스에 캐릭터 정보를 추가
            self.db.add_character(character)

        # 마지막 페이지는 nextCursor 가 None이다.
        # 따라서 마지막 페이지라면 플래그 변수 done을 True로 하고, 종료
        if resp["data"]["nextCursor"] is None:
            print("마지막 페이지")
            self.done = True
            return
        
    # 크롤링을 진행하는 메서드
    async def crawl(self, page: Page):

        # 이벤트 리스너 등록
        # 페이지에서 발생하는 모든 HTTP응답을 감지
        # 서버로부터 응답이 올때마다 handle_response 메서드 호출
        page.on("response", self.handle_response)
        try:
            # 뤼튼 캐릭터 페이지로 이동
            await page.goto("https://wrtn.ai/character/explore")

            # 크롤링 루프
            # self.done 이 True가 아니라면 반복
            while not self.done:
                
                await asyncio.sleep(self.SCROLL_DELAY)              # 2초 딜레이를 줌
                await page.evaluate_handle(SCROLL_DOWN_SCRIPT)      # 가장 앞에 정의한 SCROLL_DOWN_SCRIPT 를 이용해 아래로 스크롤 (스크롤 내려야 캐릭터들이 로드됨)
        
        # finally 구문은 반드시 실행
        # 크롤링이 완료되면 리스너 제거
        finally:
            page.remove_listener("response", self.handle_response)
