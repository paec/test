from typing import TypedDict, List

from langchain_openai import ChatOpenAI

from langchain_core.messages import (

    SystemMessage,

    HumanMessage,

    BaseMessage,

    AIMessage,

)

from langchain_core.tools import tool

from langgraph.graph import StateGraph, START, END

from langgraph.prebuilt import ToolNode

# ======================

# 1. 定義 State：只有 messages

# ======================

class AgentState(TypedDict):

    messages: List[BaseMessage]

# ======================

# 2. 定義工具（LLM「可選擇」呼叫）

# ======================

MENU = ["珍珠奶茶", "紅茶拿鐵", "綠茶"]

OUT_OF_STOCK = ["紅茶拿鐵"]

@tool

def check_inventory_tool(drink: str) -> str:

    """查詢飲料是否有庫存，回傳狀態文字。"""

    if drink in OUT_OF_STOCK:

        return f"{drink} 目前缺貨"

    if drink in MENU:

        return f"{drink} 有庫存"

    return f"菜單裡沒有 {drink} 這個品項"

tools = [check_inventory_tool]

# ======================

# 3. 初始化 LLM 並綁定 tools

# ======================

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

model_with_tools = llm.bind_tools(tools)

# ======================

# 4. Agent node：在這裡實際 invoke LLM

# ======================

def agent_node(state: AgentState) -> AgentState:

    messages = state["messages"]

    # 這一行就是實際的「給 prompt + call LLM」

    response = model_with_tools.invoke(messages)

    # 把 LLM 的回覆接在 message 後面

    return {"messages": messages + [response]}

# ======================

# 5. Tool node：執行 LLM 要求的 tool_calls

# ======================

tool_node = ToolNode(tools=tools)

# ======================

# 6. Router：決定下一步要去 tools 還是結束

# ======================

def should_continue(state: AgentState) -> str:

    last_msg = state["messages"][-1]

    # 如果最後一則是 AIMessage 且有 tool_calls，就去 tools

    if isinstance(last_msg, AIMessage) and last_msg.tool_calls:

        return "tools"

    # 否則流程結束

    return "end"

# ======================

# 7. 建立 Graph

# ======================

builder = StateGraph(AgentState)

builder.add_node("agent", agent_node)

builder.add_node("tools", tool_node)

builder.add_edge(START, "agent")

builder.add_conditional_edges(

    "agent",

    should_continue,

    {

        "tools": "tools",

        "end": END,

    },

)

builder.add_edge("tools", "agent")

graph = builder.compile()

# ======================

# 8. ★ 這裡就是你剛說「缺少」的 initial messages ★

# ======================

initial_messages = [

    SystemMessage(

        content=(

            "你是飲料店店員。"

            "如果需要確認某個飲料的庫存，可以呼叫工具 check_inventory_tool。"

            "最後請用簡短中文回答使用者。"

        )

    ),

    HumanMessage(

        content="我要一杯半糖少冰的紅茶拿鐵，現在有嗎？"

    ),

]

initial_state: AgentState = {"messages": initial_messages}

# ======================

# 9. 執行 Graph

# ======================

result_state = graph.invoke(initial_state)

for m in result_state["messages"]:

    print(type(m), ":", m.content)
