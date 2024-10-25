# models.py

from dataclasses import dataclass # dataclass 데코레이터 (자동으로 초기화 메서드와 기타 메서드를 생성)
from typing import List, Optional # List와 Optional 타입

 
@dataclass            # 클래스에 dataclass 데코레이터를 적용
class Character:      # Character라는 이름의 데이터 클래스를 정의

    wrtn_id: str                       # 뤼튼 고유 ID
    name: str                          # 캐릭터 이름
    description: str                   # 캐릭터 설명
    profile_url: Optional[str]         # 프로필 이미지 URL
    profile_image: Optional[bytes]     # 프로필 이미지 URL의 바이트 형식
    author: str                        # 캐릭터 제작자
    initial_message: str               # 첫 메시지
    categories: List[str]              # 카테고리
