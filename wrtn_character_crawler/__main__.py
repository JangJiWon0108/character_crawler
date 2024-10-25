# __main.py__ 

# .env 파일에서 환경 변수 불러옴
import os
import dotenv
dotenv.load_dotenv()

import asyncio
from playwright.async_api import async_playwright, Playwright

from wrtn_character_crawler.crawler import Crawler
from wrtn_character_crawler.database import DBConfig, Database

# 비동기 크롤러 작업을 실행하는 함수
async def run(playwright: Playwright):
    browser = await playwright.chromium.launch()  # Chromium 브라우저를 비동기로 실행
    context = await browser.new_context()         # 브라우저의 새로운 컨텍스트(탭)을 만듬

    # 리소스 사용을 줄이기 위해 이미지 로드 비활성화
    # https://github.com/microsoft/playwright-python/issues/955
    await context.route(
        "**/*",
        lambda route: (
            route.abort()
            if route.request.resource_type == "image"
            else route.continue_()
        ),
    )

    # 데이터베이스 객체 생성 (환경 변수를 통해 유저 이름, 비밀번호, DB 정보 가져옴)
    db = Database(DBConfig(
        host="database",                 # yaml 파일에서 데이터베이스 서비스 이름 - database임
        user=os.environ["DB_USER"],      # 유저 이름
        password=os.environ["DB_PASS"],  # 패스워드
        database="wrtn_db"               # db이름 (yaml 파일에서 정의됨)
    ))

    # 크롤러 객체 생성
    crawler = Crawler(db)

    try:
        page = await context.new_page()    # 새 페이지 열기
        await crawler.crawl(page)          # 크롤링 수행(crawler의 crawl 메서드 호출)
    finally:
        db.close()                         # 크롤링이 끝나면 데이터베이스 연결을 닫음
        await context.close()              # 브라우저 컨텍스트 닫기
        await browser.close()              # 브라우저 종료


# 메인 함수로, 크롤러 작업을 실행하는 엔트리 포인트
async def main():
    print("Crawler Started")                        # 크롤러 시작 메시지를 출력
    
    # 비동기 Playwright 사용 (자동으로 Playwright 리소스를 관리해줌)
    async with async_playwright() as playwright:
        await run(playwright)


# 비동기 메인 함수를 실행하여 크롤링 작업을 시작
asyncio.run(main())
