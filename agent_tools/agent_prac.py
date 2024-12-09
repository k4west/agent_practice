from dotenv import load_dotenv
from langsmith import traceable
import os
from custom_tools import search_news, python_repl_tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import AgentExecutor


load_dotenv()
os.environ["LANGCHAIN_PROJECT"] = "agents"
tools = [search_news, python_repl_tool]


# 프롬프트 생성
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful assistant. "
            "Make sure to use the `query_news` tool for searching keyword related news.",
        ),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)

# LLM 정의
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Agent 생성
agent = (create_tool_calling_agent(llm, tools, prompt))

# AgentExecutor 생성
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=10,
    max_execution_time=10,
    handle_parsing_errors=True,
)

@traceable
def run_agent_executor(query):
    return agent_executor.invoke({"input": query})

query = "AI 투자와 관련된 뉴스를 검색해 주세요."
result = run_agent_executor(query)
print("Agent 실행 결과:")
print(result["output"])
