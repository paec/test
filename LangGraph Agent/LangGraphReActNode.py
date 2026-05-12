"""
# 教學綱要：ReAct Agent 在這個檔案中幫你處理了什麼？

本範例使用 `langgraph.prebuilt.create_react_agent` 建立 ReAct Agent，
讓你**不需要自己管理對話狀態與工具呼叫流程**。

## ReAct Node 已自動處理的事情
- AIMessage、ToolMessage 的產生與順序
- 工具呼叫（Action）與工具回傳結果（Observation）
- 將工具結果自動回饋給 LLM 再繼續推理
- messages list 的增量累積（conversation history） (AIMessage、ToolMessage)
- 直到產生最終回覆（Final Answer）

你只需要：
- 提供初始 `HumanMessage`
- 在最後讀取 `result["messages"][-1]`

> 一般用 ReAct Node 就夠了；真的要控流程時，再自己下場寫 conditional edge 配 Tool Node。
> 可參考 LangGraphAgent_Examaple1.py

"""


from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

MENU = ["珍珠奶茶", "娜杯紅茶拿鐵", "綠茶"]

@tool
def match_drink(user_text: str) -> str:
    """從使用者輸入中找最可能的飲料品項，找不到回 UNKNOWN。"""
    for item in MENU:
        if item in user_text:
            return item
    return "UNKNOWN"

@tool
def extract_pref(user_text: str) -> dict:
    """提取糖度與冰量。"""
    sugar = "微糖" if "微糖" in user_text else "正常"
    ice = "少冰" if "少冰" in user_text else "正常"
    return {"sugar": sugar, "ice": ice}

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

agent = create_react_agent(
    model=llm,
    tools=[match_drink, extract_pref],
    prompt=(
        "你是飲料店點單助手。"
        "先用工具判斷 drink，再提取 sugar/ice。"
        "若 drink=UNKNOWN，先請使用者確認品項，不要猜。"
        "最後用簡短中文回答。"
    ),
)

result = agent.invoke(
    {"messages": [HumanMessage(content="我想要一杯娜杯紅茶拿鐵 微糖少冰")]}
)

print(result["messages"][-1].content)