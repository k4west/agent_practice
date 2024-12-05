'''
tool을 만들어서 리스트로 묶어서
llm.bind_tools(tools)를 하면 llm이 tool를 선택하는 모델이 됨

.tool_calls 를 통해서나
JsonOutputToolsParser(tools=tools)를 연결해서 
도구 사용 결과를 확인할 수 있음

execute_tool_calls 함수를 정의해서 도구를 사용하도록 할 수 있고,
agent를 사용할 수 있다.

agent 예)
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
)
result = agent_executor.invoke({"input": query})
print(result["output"])
'''

from dotenv import load_dotenv
from langchain_teddynote import logging

from langchain.agents import tool
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers.openai_tools import JsonOutputToolsParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent
from langchain.agents import AgentExecutor

load_dotenv()
logging.langsmith("agent-bind-tools")

@tool
def tool1():
    return

@tool
def tool2():
    return

@tool
def tool3():
    return

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
tools = [tool1, tool2, tool3]
llm_with_tools = llm.bind_tools(tools)


'''도구 호출 결과 확인'''
query = ""
print("도구 호출 결과 확인")
print(llm_with_tools.invoke(query).tool_calls)
# [{
#     'name': 'get_word_length',  
#     'args': {'word': 'teddynote'},  
#     'id': 'call_ReeUlCuSd35Marox3yaxMgcH',  
#     'type': 'tool_call'
# }]

# 도구 바인딩 + 도구 파서
chain = llm_with_tools | JsonOutputToolsParser(tools=tools)
tool_call_results = chain.invoke("What is the length of the word 'teddynote'?")
print(tool_call_results)


def execute_tool_calls(tool_call_results):
    """
    도구 호출 결과를 실행하는 함수

    :param tool_call_results: 도구 호출 결과 리스트
    :param tools: 사용 가능한 도구 리스트
    """
    # 도구 호출 결과 리스트를 순회합니다.
    for tool_call_result in tool_call_results:
        # 도구의 이름과 인자를 추출합니다.
        tool_name = tool_call_result["type"]
        tool_args = tool_call_result["args"]

        # 도구 이름과 일치하는 도구를 찾아 실행합니다.
        # next() 함수를 사용하여 일치하는 첫 번째 도구를 찾습니다.
        matching_tool = next((tool for tool in tools if tool.name == tool_name), None)

        if matching_tool:
            # 일치하는 도구를 찾았다면 해당 도구를 실행합니다.
            result = matching_tool.invoke(tool_args)
            # 실행 결과를 출력합니다.
            print(f"[실행도구] {tool_name}\n[실행결과] {result}")
        else:
            # 일치하는 도구를 찾지 못했다면 경고 메시지를 출력합니다.
            print(f"경고: {tool_name}에 해당하는 도구를 찾을 수 없습니다.")


chain = llm_with_tools | JsonOutputToolsParser(tools=tools) | execute_tool_calls
chain.invoke(query)


# Agent프롬프트 생성
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are very powerful assistant, but don't know current events",
        ),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

# 모델 생성
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Agent 생성
agent = create_tool_calling_agent(llm, tools, prompt)

# AgentExecutor 생성
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
)

# Agent 실행
result = agent_executor.invoke({"input": query})

# 결과 확인
print(result["output"])