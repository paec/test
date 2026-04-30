from typing import List, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

# ============================================
# LangGraph + LLM 工具調用範例
# ============================================
# 展示如何用LangGraph搭配LLM，讓AI自動判斷何時呼叫工具
# 流程：User提問 → Agent判斷 → 決定是否調用工具 → 執行工具 → 回報結果 → 生成答案


# ============================================
# 定義Agent的狀態 (State)
# ============================================
# AgentState用來存儲Agent對話過程中的所有信息
# 在LangGraph中，State會在各個節點間流轉和更新
class AgentState(TypedDict):
    # messages: 對話歷史記錄
    # 這是一個BaseMessage列表，會不斷追加新的消息
    # 內容包括：
    #   - SystemMessage: 系統提示（定義Agent角色、能力等）
    #   - HumanMessage: 使用者輸入
    #   - AIMessage: 模型輸出（包括決定是否調用工具）
    #   - ToolMessage: 工具執行結果
    # 例如流程中messages會逐漸變成：
    # [
    #   SystemMessage(content="你是飲料店店員..."),
    #   HumanMessage(content="我要紅茶拿鐵嗎？"),
    #   AIMessage(content="...", tool_calls=[...]),  # AI決定調用工具
    #   ToolMessage(content="紅茶拿鐵 目前缺貨"),     # 工具執行結果
    #   AIMessage(content="抱歉紅茶拿鐵缺貨...")      # AI最終回答
    # ]
    messages: List[BaseMessage]


# ============================================
# 店鋪數據
# ============================================
MENU = ["珍珠奶茶", "紅茶拿鐵", "綠茶"]      # 菜單上的飲料
OUT_OF_STOCK = ["紅茶拿鐵"]                # 目前缺貨的飲料


# ============================================
# 定義工具 (Tool)
# ============================================
# @tool 裝飾器將普通函數轉換為LangChain工具
# 工具信息會被自動抽取（包括函數名、參數類型、docstring）
# 這些信息會被發送給LLM，讓LLM知道有哪些工具可以調用
@tool
def check_inventory_tool(drink: str) -> str:
    """查詢飲料是否有庫存，回傳狀態文字。"""
    if drink in OUT_OF_STOCK:
        return f"{drink} 目前缺貨"
    if drink in MENU:
        return f"{drink} 有庫存"
    return f"菜單裡沒有 {drink} 這個品項"


tools = [check_inventory_tool]  # 工具列表

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# ============================================
# bind_tools 的魔法
# ============================================
# bind_tools() 將工具綁定到模型上，做了以下事情：
# 1. 從工具的函數簽名和docstring中提取元信息
#    - 工具名稱：check_inventory_tool
#    - 參數名和類型：drink 是 str
#    - 工具描述：docstring 的內容
# 2. 將這些信息格式化並通過系統提示發送給LLM
# 3. 在LLM的輸出中啟用 tool_calls 格式
#    - 當LLM決定要調用工具時，會在回應中包含 tool_calls
#    - tool_calls 格式如：{"name": "check_inventory_tool", "args": {"drink": "紅茶拿鐵"}}
# 4. 返回一個「工具感知」的模型，可以理解何時/如何調用工具
model_with_tools = llm.bind_tools(tools)


# ============================================
# Agent節點 (調用LLM)
# ============================================
# 這是LangGraph中的第一個節點，負責讓LLM進行推理和決策
def agent_node(state: AgentState) -> AgentState:
    # 從State中取出所有過往的消息
    # messages 是一個List[BaseMessage]，包含從開始到現在的所有對話
    messages = state["messages"]
    
    # model_with_tools.invoke(messages) 做了什麼：
    # 1. 將整個 messages 列表發送給 OpenAI API
    # 2. OpenAI看到了系統提示（知道自己是店員）和可用的工具
    # 3. 根據對話內容，模型決定：
    #    a) 直接回答（如果不需要查詢信息）
    #    b) 調用工具（如果需要查詢庫存）
    # 4. 返回一個 AIMessage 對象，包含：
    #    - content: 文字回應
    #    - tool_calls: 如果決定調用工具，這裡會有工具調用信息
    #      格式：[{"id": "call_xxx", "name": "check_inventory_tool", "args": {...}}]
    response = model_with_tools.invoke(messages)
    
    # 將LLM的回應加到消息列表中
    # 完整的流程是不斷累積 messages，讓LLM能看到完整的上下文
    return {"messages": messages + [response]}


# ============================================
# 工具節點 (執行工具)
# ============================================
# ToolNode 是 LangGraph 預先構建的節點
# 功能：檢查上一個消息的 tool_calls，自動執行對應的工具
# 過程：
# 1. 檢查前一個 AIMessage 是否有 tool_calls
# 2. 如果有，根據 tool_calls 中的工具名和參數執行工具
# 3. 為每個工具調用生成一個 ToolMessage，包含執行結果
# 4. 將 ToolMessage 加到 messages 中
tool_node = ToolNode(tools=tools)


# ============================================
# 條件邊函數 (決定下一步去哪)
# ============================================
# 這個函數用於決策：Agent的回應後，應該進行什麼操作？
def should_continue(state: AgentState) -> str:
    # 獲取最後一條消息（最新的 AIMessage）
    last_msg = state["messages"][-1]
    
    # 判讀邏輯：
    # 1. 檢查最後一條消息是否是 AIMessage（來自LLM）
    # 2. 檢查是否有 tool_calls（LLM決定調用工具的信號）
    # 3. 如果兩個條件都滿足，返回 "tools" → 去執行工具節點
    # 4. 否則返回 "end" → 結束對話
    if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
        return "tools"  # 有工具調用，去工具節點執行
    return "end"       # 無工具調用，LLM已給出最終答案，結束


# ============================================
# 構建LangGraph流程圖
# ============================================
# StateGraph 定義了Agent的執行流程
builder = StateGraph(AgentState)

# 添加兩個節點
builder.add_node("agent", agent_node)  # 節點1：調用LLM
builder.add_node("tools", tool_node)   # 節點2：執行工具

# 設置開始邊：START → agent（每次執行都從agent節點開始）
builder.add_edge(START, "agent")

# 設置條件邊：agent → (tools or END)
# should_continue 函數決定去向
# 如果返回 "tools" → 去 tools 節點
# 如果返回 "end" → 結束為 END
builder.add_conditional_edges(
    "agent",
    should_continue,
    {"tools": "tools", "end": END}
)

# 設置工具邊：tools → agent（執行工具後，回到agent讓LLM看到結果）
# 這形成了一個循環：
# - agent 調用 LLM → 決定調用工具
# - tools 執行工具 → 獲得結果
# - 回到 agent → LLM看到工具結果，進行下一步推理
builder.add_edge("tools", "agent")

# 編譯圖（將抽象建構編譯成可執行的計算圖）
graph = builder.compile()


# ============================================
# 執行例子
# ============================================
def run_example() -> None:
    # 構建初始消息列表
    initial_messages = [
        # SystemMessage：系統角色定義
        # 告訴LLM它扮演什麼角色、應該做什麼、有哪些能力
        SystemMessage(
            content=(
                "你是飲料店店員。"
                "如果需要確認某個飲料的庫存，可以呼叫工具 check_inventory_tool。"
                "最後請用簡短中文回答使用者。"
            )
        ),
        # HumanMessage：使用者提問
        # 這是對話的起點
        HumanMessage(content="我要一杯半糖少冰的紅茶拿鐵，現在有嗎？"),
    ]
    
    # 建立初始State
    # 這個State會被傳入 graph.invoke()，開始啟動流程
    initial_state: AgentState = {"messages": initial_messages}
    
    # 執行圖
    # graph.invoke() 會：
    # 1. 把 initial_state 傳給 agent 節點
    # 2. agent 節點調用 LLM（傳入所有 messages）
    # 3. LLM 看到用戶想要紅茶拿鐵，決定調用 check_inventory_tool
    # 4. should_continue 返回 "tools"，進入 tools 節點
    # 5. tools 節點執行 check_inventory_tool("紅茶拿鐵")
    # 6. 將結果（"紅茶拿鐵 目前缺貨"）包裝成 ToolMessage 加入 messages
    # 7. 再次進入 agent 節點（tools → agent 邊）
    # 8. LLM 看到工具結果，生成最終回答
    # 9. should_continue 返回 "end"，流程結束
    result_state = graph.invoke(initial_state)\n    
    # 打印最終結果\n    # 輸出每條消息的類型和內容\n    # 會看到消息流的完整演化過程：\n    # 1. SystemMessage - 角色定義\n    # 2. HumanMessage - 用戶提問\n    # 3. AIMessage - LLM決定調用工具\n    # 4. ToolMessage - 工具執行結果\n    # 5. AIMessage - LLM最終回答\n    for message in result_state["messages"]:\n        print(type(message).__name__, \":\", message.content)\n\n\nif __name__ == \"__main__\":\n    # 執行示例\n    run_example()
