"""
Agent 化做法：讓 agent 自主調用「品項比對工具」，準確判斷飲料品名
相比固定流程，這種做法：
1. Agent 自主決策何時查詢品項
2. 如果不確定，可以主動確認用戶
3. 易於擴充：只需新增工具，不用改 prompt
"""

from typing import List, TypedDict
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from difflib import SequenceMatcher


# ============================================
# 菜單數據（易於維護、擴充）
# ============================================
MENU = {
    "珍珠奶茶": ["珍奶", "珍珠奶茶"],
    "娜杯紅茶拿鐵": ["娜杯紅茶拿鐵", "娜杯紅茶", "紅茶拿鐵"],
    "綠茶": ["綠茶"],
    "奶蓋茶": ["奶蓋茶", "奶蓋"],
}

SUGAR_OPTIONS = ["正常", "半糖", "微糖", "無糖"]
ICE_OPTIONS = ["正常", "少冰", "去冰"]


# ============================================
# Agent 狀態
# ============================================
class OrderAgentState(TypedDict):
    user_input: str
    messages: List[BaseMessage]
    order: dict  # {"drink": str, "sugar": str, "ice": str}
    confirmed: bool


# ============================================
# 工具 1：模糊匹配飲料品項
# ============================================
@tool
def match_drink_fuzzy(user_text: str) -> str:
    """
    從用戶輸入中模糊匹配飲料品項。
    回傳最匹配的菜單品項名稱，如果無法確定回傳 "UNKNOWN"。
    """
    best_match = None
    best_score = 0.6  # 相似度門檻
    
    # 檢查直接包含
    for official_name, aliases in MENU.items():
        for alias in aliases:
            if alias in user_text:
                return official_name
    
    # 如果沒有直接匹配，用相似度比對
    for official_name, aliases in MENU.items():
        for alias in aliases:
            ratio = SequenceMatcher(None, user_text.lower(), alias.lower()).ratio()
            if ratio > best_score:
                best_score = ratio
                best_match = official_name
    
    return best_match if best_match else "UNKNOWN"


# ============================================
# 工具 2：解析糖度和冰量
# ============================================
@tool
def extract_sugar_ice(user_text: str) -> dict:
    """
    從用戶輸入中提取糖度和冰量偏好。
    回傳 {"sugar": str, "ice": str}。
    """
    sugar = "正常"
    ice = "正常"
    
    # 檢查糖度
    for opt in SUGAR_OPTIONS:
        if opt in user_text:
            sugar = opt
            break
    
    # 檢查冰量
    for opt in ICE_OPTIONS:
        if opt in user_text:
            ice = opt
            break
    
    return {"sugar": sugar, "ice": ice}


# ============================================
# 工具 3：確認訂單
# ============================================
@tool
def confirm_order(drink: str, sugar: str, ice: str) -> str:
    """確認訂單信息，回傳確認文字。"""
    if drink == "UNKNOWN":
        return f"抱歉，菜單裡沒有找到這個品項。我們有：{', '.join(MENU.keys())}"
    return f"✓ 已確認訂單：{sugar}、{ice} 的 {drink}"


tools = [match_drink_fuzzy, extract_sugar_ice, confirm_order]

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
model_with_tools = llm.bind_tools(tools)


# ============================================
# Agent 節點
# ============================================
def agent_node(state: OrderAgentState) -> OrderAgentState:
    """
    Agent 自主決策：
    1. 理解用戶需求
    2. 決定何時調用工具進行品項比對、糖度冰量解析、訂單確認
    3. 最後給出回答
    """
    messages = state["messages"]
    
    # Agent 的系統提示：定義角色、目標、可用工具
    system_prompt = f"""
你是一個飲料店智能點單助手。
目標：從客戶的語音/文字輸入中理解飲料需求，準確判斷品項、糖度、冰量。

目前菜單品項：{', '.join(MENU.keys())}

執行步驟：
1. 先用 match_drink_fuzzy 從用戶輸入匹配品項
2. 用 extract_sugar_ice 提取糖度和冰量
3. 用 confirm_order 確認整個訂單

如果品項不確定，先問用戶，不要猜測。
最後用簡短中文回答用戶。
"""
    
    # 將系統提示加入消息列表開頭
    messages_with_system = [SystemMessage(content=system_prompt)] + messages
    
    # 調用 LLM（帶工具綁定）
    response = model_with_tools.invoke(messages_with_system)
    
    return {
        "user_input": state["user_input"],
        "messages": messages + [response],
        "order": state.get("order", {}),
        "confirmed": state.get("confirmed", False)
    }


# ============================================
# 工具節點（執行工具）
# ============================================
tool_node = ToolNode(tools=tools)


# ============================================
# 條件邊：決定是否繼續循環
# ============================================
def should_continue(state: OrderAgentState) -> str:
    last_msg = state["messages"][-1]
    
    if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
        return "tools"  # 還有工具調用，去執行
    return "end"       # 無工具調用，LLM 已給出答案


# ============================================
# 構建 LangGraph
# ============================================
builder = StateGraph(OrderAgentState)

builder.add_node("agent", agent_node)
builder.add_node("tools", tool_node)

builder.add_edge(START, "agent")
builder.add_conditional_edges(
    "agent",
    should_continue,
    {"tools": "tools", "end": END}
)
builder.add_edge("tools", "agent")

graph = builder.compile()


# ============================================
# 執行範例
# ============================================
def run_example() -> None:
    test_cases = [
        "我想要一杯娜杯紅茶拿鐵 微糖少冰",
        "來杯珍奶 半糖",
        "我要奶蓋茶",
        "給我紅茶拿鐵去冰",
    ]
    
    for user_input in test_cases:
        print("\n" + "="*50)
        print(f"📝 用戶輸入：{user_input}")
        print("="*50)
        
        initial_messages = [
            HumanMessage(content=user_input)
        ]
        
        initial_state: OrderAgentState = {
            "user_input": user_input,
            "messages": initial_messages,
            "order": {},
            "confirmed": False
        }
        
        result_state = graph.invoke(initial_state)
        
        # 打印消息流
        print("\n📋 完整消息流：")
        for msg in result_state["messages"]:
            msg_type = type(msg).__name__
            content = msg.content if hasattr(msg, "content") else str(msg)
            print(f"  [{msg_type}] {content[:100]}...")
        
        # 打印最終回答
        last_msg = result_state["messages"][-1]
        if isinstance(last_msg, AIMessage):
            print(f"\n✅ 最終回答：{last_msg.content}")


if __name__ == "__main__":
    run_example()
