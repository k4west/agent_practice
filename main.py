from dotenv import load_dotenv
from langchain_teddynote import logging
import warnings

load_dotenv()
logging.langsmith("agent-practice")
warnings.filterwarnings("ignore") # 경고 메시지 무시