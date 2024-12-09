from dotenv import load_dotenv
from langchain_teddynote import logging
import warnings

import requests
from lxml import html
from typing import List
from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper
from langchain.tools import tool


from typing import Annotated
from langchain_experimental.utilities import PythonREPL

# load_dotenv()
# logging.langsmith("agent-tools")
# warnings.filterwarnings("ignore") # 경고 메시지 무시


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


def get_context(link):
    response = requests.get(link)
    response.content
    return ''


@tool
def get_popular_news():
    '''
    get_popular_news
    '''
    response = requests.get('https://news.naver.com/main/ranking/popularDay.naver')
    if response.status_code != 200:
        print(response)
        return {}, {}
    popular_news = {} # 번호: [{링크, 제목}, ...]
    press_info = {} # 언론사: 번호
    office_cards = html.fromstring(response.content).xpath('//*[contains(@class, "_officeCard _officeCard")]')
    for office_card in office_cards:
        for item in office_card.xpath("div"):
            press_num = item.xpath('a')[0].attrib['href'].split('com/press/')[1][:3] # https://media.naver.com/press/{press_num}/ranking?type=popular
            press_name = item.xpath("a/*[@class='rankingnews_name']")[0].text
            press_info[press_name] = press_num
            popular_news[press_num] = []
            for li in item.xpath('ul/li/div/a'):
                link = li.attrib["href"]
                title = li.text
                popular_news[press_num].append({"link": link, "title": title})
                # context = get_context(link)
                # popular_news[press_num].append({"link": link, "title": title, "context": context})
    return popular_news, press_info


@tool
def query_news(query):
    '''query_news'''
    params = {
        'where': 'news',
        'ie': 'utf8',
        'sm': 'nws_hty',
        'query': query,
    }
    response = requests.get('https://search.naver.com/search.naver', params=params)
    if response.status_code != 200:
        print(response)
        return {}, {}
    news = {} # 번호: [{링크, 제목}, ...]
    press_info = {} # 언론사: 번호
    sections = html.fromstring(response.content).xpath('//*[@id="main_pack"]/section//*[contains(@class, "news_area")]')
    for section in sections:
        items = section.xpath("div")
        info = items[0].xpath('div[2]/a')
        press_name = info[0].text_content().strip()
        link = [i.attrib.get('href', '') for i in info if 'naver' in i.attrib.get('href', '')]
        if link:
            link = link[0]
        else:
            link = 'article/'
        press_num = link.split('article/')[1][:3]
        title = [i.attrib.get('title', '') for i in items[1].xpath('a') if i.attrib.get('title', '')][0]
        if press_name not in press_info:
            press_info[press_name] = press_num
            news[press_num or press_name] = []
        # news[press_num or press_name].append({"link": link, "title": title})
        context = get_context(link) if 'naver' in link else items[1].xpath('div')[0].text_content()
        news[press_num or press_name].append({"link": link, "title": title, "context": context})
    return news, press_info


# 도구 생성
@tool
def python_repl_tool(
    code: Annotated[str, "The python code to execute to generate your chart."],
):
    """Use this to execute python code. If you want to see the output of a value,
    you should print it out with `print(...)`. This is visible to the user."""
    result = ""
    try:
        result = PythonREPL().run(code)
    except BaseException as e:
        print(f"Failed to execute. Error: {repr(e)}")
    finally:
        return result
    

@tool
def search_news(query):
    """
    Search Naver News by input keyword
    """
    params = {
        'where': 'news',
        'ie': 'utf8',
        'sm': 'nws_hty',
        'query': query,
    }
    response = requests.get('https://search.naver.com/search.naver', params=params)
    if response.status_code != 200:
        print(response)
        return {}, {}
    news = {} # 번호: [{링크, 제목}, ...]
    press_info = {} # 언론사: 번호
    sections = html.fromstring(response.content).xpath('//*[@id="main_pack"]/section//*[contains(@class, "news_area")]')
    for section in sections:
        items = section.xpath("div")
        info = items[0].xpath('div[2]/a')
        press_name = info[0].text_content().strip()
        link = [i.attrib.get('href', '') for i in info if 'naver' in i.attrib.get('href', '')]
        if link:
            link = link[0]
        else:
            link = 'article/'
        press_num = link.split('article/')[1][:3]
        title = [i.attrib.get('title', '') for i in items[1].xpath('a') if i.attrib.get('title', '')][0]
        if press_name not in press_info:
            press_info[press_name] = press_num
            news[press_num or press_name] = []
        news[press_num or press_name].append({"link": link, "content": title})
    # return news, press_info
    result = sum([*news.values()], [])
    return result


