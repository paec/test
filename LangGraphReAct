"""

最小可跑 ReAct + LangGraph 範例（單檔版）

重點：

- 用 LangGraph 建一個有 loop 的 graph

- agent_step：LLM 讀 state，決定「呼叫工具 or 結束」

- tool_node：真的去查工具（這裡先用假工具），再回 agent_step

- 反覆迴圈，直到 LLM 說「可以給最終答案」為止

"""

from future import annotations

from typing import TypedDict, Literal, Any, List, Dict, Optional

# ========== 0. 準備 LLM（你可以依照自己環境調整） ==========

from langchain_openai import ChatOpenAI

from langchain_core.messages import AIMessage, HumanMessage

# 這裡以 OpenAI / Compatible API 為例，請替換成你的設定

# 例如：

#   export OPENAI_API_KEY=...

#   export OPENAI_BASE_URL=...

llm = ChatOpenAI(

    model="gpt-4o-mini",  # 或其他你有的模型名稱

    temperature=0.2,

)

# ========== 1. 定義 State：在 LangGraph 裡要傳來傳去的「資料容器」 ==========

class AgentState(TypedDict, total=False):

    """

    整個 Agent 在 ReAct 迴圈中所有要記錄的狀態。

    LangGraph 每跑一個 node，就會把這個 state 當作 input/output。

    """

    # 使用者的原始問題（這個通常不變）

    user_input: str

    # ReAct 過程中的 log（Thought / Action / Observation 等）

    history: List[str]

    # 最近一次工具查詢的結果（讓 LLM 再看一次）

    tool_result: Any | None

    # LLM 判斷目前狀態：還在思考中，還是已經可以結束

    status: Literal["thinking", "done"]

    # 最終要回給使用者的答案（當 status == "done" 時應該要有）

    final_answer: Optional[str]

    # 如果 LLM 決定要呼叫工具，會把想查的內容放在這裡，給 tool_node 用

    pending_tool_query: Optional[str]

# ========== 2. 一些簡單字串解析工具（弱 parsing，示範用） ==========

def extract_between(text: str, start_key: str, end_keys: List[str]) -> str:

    """

    從 text 裡面，抓出 start_key 和任何一個 end_key 之間的內容。

    假設格式像：

      Thought: ......

      Action: use_tool

    就可以用：

      extract_between(raw, "Thought:", ["Action:", "Final:"])

    """

    start_idx = text.find(start_key)

    if start_idx == -1:

        return ""

    start_idx += len(start_key)

    # 找離 start_idx 最近的 end_key

    sub = text[start_idx:]

    end_idx = len(sub)

    for k in end_keys:

        i = sub.find(k)

        if i != -1 and i < end_idx:

            end_idx = i

    return sub[:end_idx].strip()

def extract_after(text: str, key: str) -> str:

    """

    從 text 裡抓出 key 後面到結尾的內容。

    例如：

      Final: 這是答案

    就可以用：

      extract_after(raw, "Final:")

    """

    idx = text.find(key)

    if idx == -1:

        return ""

    idx += len(key)

    return text[idx:].strip()

# ========== 3. agent_step：LLM inside loop 的核心 node ==========

def agent_step(state: AgentState) -> AgentState:

    """

    這個 node 的工作：

    - 查看目前的 state（包含：user_input, history, tool_result）

    - 丟給 LLM，請它用 ReAct 風格思考：

        - 要不要再呼叫工具？（Action: use_tool）

        - 還是已經可以給出最終答案？（Final: ...）

    - 解析 LLM 的輸出，更新 state（history, status, final_answer, pending_tool_query）

    """

    history_str = "\n".join(state.get("history", []))

    tool_result = state.get("tool_result")

    tool_info = f"\n\n最近的工具結果：{tool_result}" if tool_result else ""

    prompt = f"""

你是一個 ReAct 風格的助手，會反覆：

1. 想下一步要做什麼（Thought）

2. 要嘛呼叫工具（Action），要嘛直接給出最終答案（Final）

請嚴格依照以下格式輸出（非常重要）：

- 如果還要繼續查資料：

  Thought: 你對目前情況的思考

  Action: use_tool

  Action Input: <你想查的內容，一句話描述>

- 如果已經可以回答使用者：

  Thought: 你為什麼已經可以回答

  Final: <你要回給使用者的最終答案>

不要輸出其他多餘的標籤，也不要用 Markdown。

=== 使用者問題 ===

{state["user_input"]}

=== 目前的過程 (history) ===

{history_str}{tool_info}

""".strip()

    # 呼叫 LLM

    resp = llm.invoke([HumanMessage(content=prompt)])

    raw = resp.content if isinstance(resp, AIMessage) else str(resp)

    # 解析 Thought

    thought = extract_between(raw, "Thought:", ["Action:", "Final:"])

    thought = thought or "(模型沒有給 Thought)"

    # 準備要更新的共用欄位

    new_history = list(state.get("history", []))

    new_history.append(f"Thought: {thought}")

    final_answer: Optional[str] = None

    pending_tool_query: Optional[str] = None

    status: Literal["thinking", "done"] = "thinking"

    # 判斷是 Action 還是 Final

    if "Action:" in raw:

        # 這裡簡化：只允許 use_tool 一種 action

        action_input = extract_after(raw, "Action Input:")

        pending_tool_query = action_input.strip()

        new_history.append(f"Action: use_tool, input={pending_tool_query}")

        status = "thinking"

    elif "Final:" in raw:

        final_answer = extract_after(raw, "Final:")

        new_history.append(f"Final: {final_answer}")

        status = "done"

    else:

        # 如果 LLM 格式亂掉，就直接結束，避免無限 loop

        final_answer = f"(格式錯誤，我只能先回答) 原始輸出：\n{raw}"

        new_history.append("Final: (格式錯誤，強制結束)")

        status = "done"

    # 回傳新的 state

    return {

        **state,

        "history": new_history,

        "status": status,

        "final_answer": final_answer,

        "pending_tool_query": pending_tool_query,

        # 一旦進入新一輪思考，先把舊的 tool_result 清掉（由 tool_node 再寫入新結果）

        "tool_result": None if pending_tool_query else state.get("tool_result"),

    }

# ========== 4. tool_node：實際執行「工具 / API」的 node ==========

def fake_search_api(query: str) -> str:

    """

    這裡先用假的工具，示範用。

    實務上你可以在這裡呼叫：

      - HTTP API

      - Database

      - LangChain 的工具

      - 甚至再 call 一次 LLM 當工具

    """

    # 這裡示範：根據關鍵字回不同內容

    if "天氣" in query:

        return "（假工具）今天天氣晴，氣溫 25 度。"

    if "匯率" in query:

        return "（假工具）目前 USD/TWD 約為 32.5。"

    return f"（假工具）你查了：{query}，但沒有特別資料，我只回傳原文。"

def tool_node(state: AgentState) -> AgentState:

    """

    這個 node 的工作：

    - 讀取 state["pending_tool_query"]

    - 呼叫對應工具（這裡是 fake_search_api）

    - 把結果寫入 state["tool_result"]，並加到 history

    - 清掉 pending_tool_query（代表這次工具查完了）

    """

    query = state.get("pending_tool_query")

    if not query:

        # 如果沒有要查的東西，就原樣返回（正常情況應該不會發生）

        return state

    # 呼叫假工具

    result = fake_search_api(query)

    new_history = list(state.get("history", []))

    new_history.append(f"Observation: {result}")

    return {

        **state,

        "history": new_history,

        "tool_result": result,

        "pending_tool_query": None,

    }

# ========== 5. 用 LangGraph 把 node 接成「有 loop 的 graph」 ==========

from langgraph.graph import StateGraph, END

# 建立一個 StateGraph，指定 state 類型為 AgentState

builder = StateGraph(AgentState)

# 加入兩個 node：agent_step / tool_node

builder.add_node("agent_step", agent_step)

builder.add_node("tool_node", tool_node)

# 指定入口：一開始先跑 agent_step

builder.set_entry_point("agent_step")

def route_from_agent(state: AgentState) -> str:

    """

    這個函式決定：從 agent_step 跑完後，要走到哪一個 edge。

    回傳值是一個「標籤」，會對應到 add_conditional_edges 裡的 mapping。

    """

    # 如果 LLM 已經說「done」，那就走向 "end"（對應到 END）

    if state.get("status") == "done":

        return "end"

    # 如果有 pending_tool_query，代表 LLM 想用工具 → 走向 "tool"

    if state.get("pending_tool_query"):

        return "tool"

    # 否則（沒說 done、也沒要用工具），就再讓 agent_step 想一次 → "think"

    # 這視你的設計而定，這裡只是示範。

    return "think"

# 從 "agent_step" 這個 node 出來之後，看 state 決定要走哪一條邊

builder.add_conditional_edges(

    "agent_step",

    route_from_agent,

    {

        "tool": "tool_node",   # 去工具

        "think": "agent_step", # 再想一次（沒呼叫工具也沒結束）

        "end": END,            # 結束

    }

)

# 工具跑完，一定回到 agent_step 再想一次

builder.add_edge("tool_node", "agent_step")

# compile 出真正可以執行的 graph

graph = builder.compile()

# ========== 6. 範例執行：跑一次 ReAct 迴圈看看 ==========

def run_example():

    """

    示範如何呼叫這個 ReAct Agent。

    """

    user_question = "請幫我查一下今天天氣怎樣，然後用一句話總結告訴我。"

    # 初始化 state

    init_state: AgentState = {

        "user_input": user_question,

        "history": [],

        "tool_result": None,

        "status": "thinking",

        "final_answer": None,

        "pending_tool_query": None,

    }

    # 方式一：一次跑到結束（graph.invoke）

    final_state = graph.invoke(init_state)

    print("====== 最終答案 ======")

    print(final_state.get("final_answer", "(沒有答案)"))

    print("\n====== 完整 ReAct 過程 (history) ======")

    for step in final_state.get("history", []):

        print(step)

    # 你也可以使用 stream() 逐步看每一個 node 的輸出，

    # 這裡只示範 invoke。

if name == "__main__":

    run_example()
