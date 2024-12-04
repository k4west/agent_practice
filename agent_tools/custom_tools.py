from dotenv import load_dotenv
from langchain_teddynote import logging
import warnings

import requests
from typing import List
from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper
from langchain.tools import tool

load_dotenv()
logging.langsmith("agent-tools")
warnings.filterwarnings("ignore") # 경고 메시지 무시


def generate_image(query: str, model: str="dall-e-3", size: str="1024x1024", quality: str | None="standard", n: int=1) -> str:
    '''
    DALL-E 모델로 이미지 생성하는 함수; 이미지 주소를 반환한다.

    Parameters:
        query (str): 이미지 생성을 위한 문장
        model (str): 사용할 DALL-E 모델 버전
        size (str): 이미지 크기
        quality (str | None): 이미지 품질
        n (int): 생성 이미지 수

        
    Returns:
        image_url (str): 이미지 주소

    ---
    ```python
    from agent_tools.custom_tools import generate_image
    from IPython.display import Image

    image_url = generate_image(query)
    Image(url=image_url, width=500)
    '''

    dalle = DallEAPIWrapper(model=model, size=size, quality=quality, n=n)
    image_url = dalle.run(query)
    return image_url


@tool
def crawling(query: str, must: List[str | None] = [], inclusion: List[str | None] = [], exclusion: List[str | None] = []):
    '''
    
    ...
    
    Parameters:
        query (str): 질문
        inclusion (List[str]): 포함시키고 싶은 단어(없을 수 도 있음)
        must (List[str]): 꼭 포함시키고 싶은 단어 목록
        exclusion (List[str]): 제외하고 싶은 단어 목록, 숫자는 적용이 잘 안됨

    Returns:
        ... (): ...

    ---
    ```python
    from agent_tools.custom_tools import f

    image_url = f.invoke()
    '''

    base_url = 'https://www.google.com/search?'
    params = {
        "as_q": query,
        "as_epq": " ".join(must), # ""로 감싸기
        "as_oq": " ".join(inclusion), # OR
        "as_eq": " ".join(exclusion), # 앞에 -붙이기
        'as_nlo': '',
        'as_nhi': '',
        'lr': '',
        'cr': '',
        'as_qdr': 'all',
        'as_sitesearch': '',
        'as_occt': 'any',
        'as_filetype': '',
        'tbs': '',
    }
    headers = {
        'Referer': 'https://www.google.com/',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'sec-ch-prefers-color-scheme': 'dark',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-arch': '"x86"',
        'sec-ch-ua-bitness': '"64"',
        'sec-ch-ua-form-factors': '"Desktop"',
        'sec-ch-ua-full-version': '"131.0.6778.108"',
        'sec-ch-ua-full-version-list': '"Google Chrome";v="131.0.6778.108", "Chromium";v="131.0.6778.108", "Not_A Brand";v="24.0.0.0"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-platform': '"Windows"',
        'sec-ch-ua-platform-version': '"15.0.0"',
        'sec-ch-ua-wow64': '?0',
    }
    response = requests.post(base_url, params=params, headers=headers)
    print(response.status_code) # 405
    print(response.content)
    print(response.url)
    return None


crawling.invoke({"query": '대한민국', "must": ['대통령'], "inclusion": [''], "exclusion": ['2019']})