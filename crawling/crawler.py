import os, re, html, json, requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv


with open("info.json", "r", encoding="utf-8") as f:
    info_file = json.load(f)

    file_types = info_file["file_types"]
    naver_search_api_endpoints = info_file["naver_search_api_endpoints"] # https://developers.naver.com/docs/serviceapi/search/web/web.md#%EC%9B%B9%EB%AC%B8%EC%84%9C
    daum_search_api_endpoints = info_file["daum_search_api_endpoints"] # https://developers.kakao.com/docs/latest/ko/daum-search/dev-guide

excluded_links = ["tistory", "kin", "youtube", "blog", "book", "news", "dcinside", "fmkorea", "ruliweb", "theqoo", "clien", "mlbpark", "instiz", "todayhumor"]
tag_pattern = r'<(\/?[\w\s="\':^>]*)>'

load_dotenv()
Google_API_KEY = os.getenv("Google_API_KEY") # 키 생성/가져오기: https://developers.google.com/custom-search/v1/introduction?hl=ko
Google_SEARCH_ENGINE_ID = os.getenv("Google_SEARCH_ENGINE_ID") # 검생 엔진 생성: https://programmablesearchengine.google.com/controlpanel/all
Naver_client_id = os.getenv("Naver_client_id") # https://developers.naver.com/main/
Naver_client_secret = os.getenv("Naver_client_secret")
Kakao_API_key = os.getenv("Kakao_API_key") # https://developers.kakao.com/


def remove_tags(text:str) -> str:
    text = re.sub(tag_pattern, '', text).strip()
    text = html.unescape(text)
    return text


def get_data(url, params, headers, k, items_, link_, description_):
    if headers:
        response = requests.get(url, headers=headers, params=params)
    else:
        response = requests.get(url, params=params)

    if(status_code:= response.status_code) != 200:
        print(f"Error code: {status_code}")
        return []
    
    results = []
    count = 0
    for item in response.json().get(items_, []):
        link = item.get(link_, "")
        old = int(item.get('datetime', '2023')[:4] or '2023') < 2020
        if (not link or any(ex in link for ex in excluded_links) or old):
            continue

        title = item.get("title", "no title")
        description = item.get(description_, "no description")
        title, description = map(remove_tags, (title, description))
        results.append([title, link, description] )
        count += 1
        if count >= k:
            break

    return results, count


def google_api(query:str, k:int=100, types:list[str|None]=[]) -> pd.DataFrame:
    """
    Parameters:
        query : 검색하고 싶은 검색어 
        k : 원하는 검색 결과 수 (1 ~ 300)
        types: 원하는 검색 파일 유형 목록

    Returns:
        df_google : 검색 결과
    """

    results = []
    url = "https://www.googleapis.com/customsearch/v1"
    query = query.replace("|", "OR")
    if types:
        file_types_li = sum([[*value.values()] for value in file_types.values()], [])
        query += " OR ".join([f"filetype:{type_}" for type_ in types if type_ in file_types_li]) # types에 있는 파일 형식만 검색
    params = {
        "key": Google_API_KEY,
        "cx": Google_SEARCH_ENGINE_ID,
        "q": query,
        "start": 0
    }
    k = min(300, max(int(k), 1))

    for page in range(1, k+1000, 10): # 페이지는 1부터 시작해서 각각 10개의 결과물을 보여줌.
        params["start"] = page
        results_, count = get_data(url, params, None, k, "items", "link", "snippet")
        results.extend(results_)
        if (k:=k-count) <= 0:
            break
            
    df_google = pd.DataFrame(results, columns=['Title', 'Link', 'Description'])
    return df_google


def naver_api(query:str, k:int=100, api:str="webkr", display:int=100, sort:str="sim") -> pd.DataFrame:
    """
    Parameters:
        query : 검색하고 싶은 검색어 
        k : 원하는 검색 결과 수 (1 ~ 300)
        api: 검색 api 종류 ('news', 'encyc', 'blog', 'shop', 'webkr', 'image', 'doc', 'kin', 'book', 'cafearticle', 'adult', 'errata', 'local')
        display: 한 번에 표시할 검색 결과 개수
        sort: 검색 결과 정렬 방법 ("sim": 정확도순, "date": 날짜순)

    Returns:
        df_naver : 검색 결과
    """

    results = []
    api = api if api in naver_search_api_endpoints else "webkr"
    url = f"https://openapi.naver.com/v1/search/{api}"
    headers = {
        "X-Naver-Client-Id": Naver_client_id,
        "X-Naver-Client-Secret": Naver_client_secret
    }
    # query = urllib.parse.quote(query)
    display = min(100, max(int(display), 10))
    sort = sort if sort in ["sim", "date"] else "sim"
    params = {
        "query": query,
        "display": display,
        "start": 0,
        "sort": sort
    }
    k = min(300, max(int(k), 1))

    for page in range(1, k+1000, display):
        params["start"] = page
        results_, count = get_data(url, params, headers, k, "items", "link", "description")
        results.extend(results_)
        if (k:=k-count) <= 0:
            break

    df_naver = pd.DataFrame(results, columns=['Title', 'Link', 'Description'])
    return df_naver


def daum_api(query:str, k:int, api:str="web", size:int=100, sort:str="accuracy"):
    """
    Parameters:
        query : 검색하고 싶은 검색어 
        k : 원하는 검색 결과 수 (1 ~ 300)
        api: 검색 api 종류('web', 'vclip', 'image', 'blog', 'book', 'cafe')
        size: 한 번에 표시할 검색 결과 개수
        sort: 검색 결과 정렬 방법 ("accuracy": 정확도순, "recency": 날짜순)

    Returns:
        df_daum : 검색 결과
    """

    results = []
    api = api if api in daum_search_api_endpoints else "web"
    url = f"https://dapi.kakao.com/v2/search/{api}"
    headers = {'Authorization': f'KakaoAK {Kakao_API_key}'}
    size = min(100, max(int(size), 10))
    sort = sort if sort in ["accuracy", "recency"] else "accuracy"
    params = {
        'sort': sort,
        'query' : query, 
        'page' : 0,
        'size' : size,
    }
    pages = k//size + (k%size > 0)
    k = min(300, max(int(k), 1))

    for page in range(1, pages + 10):
        params["page"] = page
        results_, count = get_data(url, params, headers, k, "documents", "url", "contents")
        results.extend(results_)
        if (k:=k-count) <= 0:
            break

    df_daum = pd.DataFrame(results, columns=['Title', 'Link', 'Description'])
    return df_daum 


def scrape(query:str, k:int, types:list[str], n_api:str, d_api:str) -> pd.DataFrame:
    today = datetime.today().strftime("%Y%m%d")

    df_google = google_api(query, k, types)
    df_google["search_engine"] = "Google"
    df_naver = naver_api(query, k, n_api)
    df_naver["search_engine"] = "Naver"
    df_daum = daum_api(query, k, d_api)
    df_daum["search_engine"] = "Daum"
    df_scrape= pd.concat([df_google, df_naver, df_daum])

    df_scrape['query'] = query
    df_scrape['fetched_date'] = today
    df_scrape.reset_index(inplace=True, drop=True)

    return df_scrape


def save2csv(df:pd.DataFrame) -> None:
    query = df["query"][0]
    query = re.sub(r"[^\uAC00-\uD7A30-9a-zA-Z\s]", "", query)
    date = df["fetched_date"][0]
    df.to_csv(f'{query}_{date}.csv', index=False, encoding="utf-8-sig")


if __name__=="__main__":
    import sys, time
    if len(sys.argv) > 1:
        query = ' '.join(sys.argv[1:])
    else:
        query = input("검색하고 싶은 내용을 입력하세요: ").strip() or "k-pop"
    s = time.time()
    k = 5
    file_type_li = []
    n_api, d_api = "webkr", "web"
    df_scrape = scrape(query, k, file_type_li, n_api, d_api)
    save2csv(df_scrape)
    print(df_scrape)
    print(time.time() - s)
    naver_search_api_endpoints_ = ["news", "encyc", "blog", "shop", "webkr", "image", "doc", "kin", "book", "cafearticle", "adult", "errata", "local"]
    daum_search_api_endpoints_ = ["web", "vclip", "image", "blog", "book", "cafe"]
