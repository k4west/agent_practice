import os
from dotenv import load_dotenv
from langsmith import traceable
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.vectorstores import FAISS
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.document_loaders import PyMuPDFLoader
from langchain.tools.retriever import create_retriever_tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.runnables.history import RunnableWithMessageHistory

load_dotenv()
os.environ["LANGCHAIN_PROJECT"] = "agents-rag"

store = {}


def get_retriever_tool(src:str) -> tuple:
    try:
        loader = PyMuPDFLoader(src)
    except Exception as e:
        print(e)
        return None
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    split_docs = loader.load_and_split(text_splitter)

    vector = FAISS.from_documents(split_docs, OpenAIEmbeddings())
    retriever = vector.as_retriever()
    retriever_tool = create_retriever_tool(
        retriever,
        name="pdf_serch",
        description="use this tool to search information from the PDF document",
    )

    return retriever_tool


def get_agent(model:str="gpt-4o-mini", temperature:int=0, system_message:str="", tools:list=[]):
    if not system_message:
        system_message = "You are a helpgul assistant. "\
                "Make sure to use the `pdf_search` tool for searching information from the PDF document. "\
                "If you can't find the information from the PDF document, use the 'search' tool for searching information form the web."

    llm = ChatOpenAI(model=model, temperature=temperature)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                system_message
            ),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )
    agent = create_tool_calling_agent(llm, tools, prompt)

    return agent


def get_session_history(session_ids):
    if session_ids not in store:
        store[session_ids] = ChatMessageHistory()
    return store[session_ids]


def agent_stream_parser(step:dict):
    nl = '\n'
    if "actions" in step:
        print("[Actions]")
        item = step["actions"][0]
        print(f"[tool]: {item.tool}")
        print(f"[query]: {item.tool_input['query']}")
        print(f"[log]: {item.log.strip()}{nl}")
    elif "steps" in step:
        item = step["steps"][0]
        print(f"[Observation]{nl}{item.observation}")
    elif "output" in step:
        item = step["output"]
        print(f"[Output]{nl}{item}")


def get_agent_with_chat_history(agent_excuter):
    agent_with_chat_history = RunnableWithMessageHistory(
        agent_excuter,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history"
    )
    return agent_with_chat_history


@traceable
def stream_agent_with_chat_history(query:str, session_id:str="asdf1234") -> None:
    response = agent_with_chat_history.stream(
        {"input": query},
        config={"configurable": {"session_id": session_id}}
    )
    for step in response:
        agent_stream_parser(step)
        # print(step)


search = TavilySearchResults(k=6)
retriever_tool = get_retriever_tool("notebooks/data/SPRI_AI_Brief_2023년12월호_F.pdf")
tools = [search, retriever_tool]
agent = get_agent(tools=tools)
agent_excuter = AgentExecutor(agent=agent, tools=tools, verbose=False)
agent_with_chat_history = get_agent_with_chat_history(agent_excuter)

query = "구글이 앤스로픽에 투자한 금액을 문서에서 찾아줘"
stream_agent_with_chat_history(query)
