"""最小可跑 ReAct + LangGraph 範例（單檔版）。"""

from __future__ import annotations

from typing import Any, List, Literal, Optional, TypedDict

from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)


class AgentState(TypedDict, total=False):
    user_input: str
    history: List[str]
    tool_result: Any | None
    status: Literal["thinking", "done"]
    final_answer: Optional[str]
    pending_tool_query: Optional[str]


def extract_between(text: str, start_key: str, end_keys: List[str]) -> str:
    start_idx = text.find(start_key)
    if start_idx == -1:
        return ""
    start_idx += len(start_key)
    sub = text[start_idx:]
    end_idx = len(sub)
    for key in end_keys:
        idx = sub.find(key)
        if idx != -1 and idx < end_idx:
            end_idx = idx
    return sub[:end_idx].strip()


def extract_after(text: str, key: str) -> str:
    idx = text.find(key)
    if idx == -1:
        return ""
    return text[idx + len(key) :].strip()


def agent_step(state: AgentState) -> AgentState:
    history_str = "\n".join(state.get("history", []))
    tool_result = state.get("tool_result")
    tool_info = f"\n\n最近的工具結果：{tool_result}" if tool_result else ""
    prompt = f"""
你是一個 ReAct 風格的助手，會反覆：
1. 想下一步要做什麼（Thought）
2. 要嘛呼叫工具（Action），要嘛直接給出最終答案（Final）

請嚴格依照以下格式輸出：
- 如果還要繼續查資料：
  Thought: 你對目前情況的思考
  Action: use_tool
  Action Input: <你想查的內容>
- 如果已經可以回答使用者：
  Thought: 你為什麼已經可以回答
  Final: <你要回給使用者的最終答案>

=== 使用者問題 ===
{state['user_input']}

=== 目前的過程 (history) ===
{history_str}{tool_info}
""".strip()

    resp = llm.invoke([HumanMessage(content=prompt)])
    raw = resp.content if isinstance(resp, AIMessage) else str(resp)

    thought = extract_between(raw, "Thought:", ["Action:", "Final:"]) or "(模型沒有給 Thought)"
    new_history = list(state.get("history", []))
    new_history.append(f"Thought: {thought}")

    final_answer: Optional[str] = None
    pending_tool_query: Optional[str] = None
    status: Literal["thinking", "done"] = "thinking"

    if "Action:" in raw:
        pending_tool_query = extract_after(raw, "Action Input:").strip()
        new_history.append(f"Action: use_tool, input={pending_tool_query}")
    elif "Final:" in raw:
        final_answer = extract_after(raw, "Final:")
        new_history.append(f"Final: {final_answer}")
        status = "done"
    else:
        final_answer = f"(格式錯誤，我只能先回答) 原始輸出：\n{raw}"
        new_history.append("Final: (格式錯誤，強制結束)")
        status = "done"

    return {
        **state,
        "history": new_history,
        "status": status,
        "final_answer": final_answer,
        "pending_tool_query": pending_tool_query,
        "tool_result": None if pending_tool_query else state.get("tool_result"),
    }


def fake_search_api(query: str) -> str:
    if "天氣" in query:
        return "（假工具）今天天氣晴，氣溫 25 度。"
    if "匯率" in query:
        return "（假工具）目前 USD/TWD 約為 32.5。"
    return f"（假工具）你查了：{query}，但沒有特別資料，我只回傳原文。"


def tool_node(state: AgentState) -> AgentState:
    query = state.get("pending_tool_query")
    if not query:
        return state
    result = fake_search_api(query)
    new_history = list(state.get("history", []))
    new_history.append(f"Observation: {result}")
    return {
        **state,
        "history": new_history,
        "tool_result": result,
        "pending_tool_query": None,
    }


builder = StateGraph(AgentState)
builder.add_node("agent_step", agent_step)
builder.add_node("tool_node", tool_node)
builder.set_entry_point("agent_step")


def route_from_agent(state: AgentState) -> str:
    if state.get("status") == "done":
        return "end"
    if state.get("pending_tool_query"):
        return "tool"
    return "think"


builder.add_conditional_edges(
    "agent_step",
    route_from_agent,
    {"tool": "tool_node", "think": "agent_step", "end": END},
)
builder.add_edge("tool_node", "agent_step")
graph = builder.compile()


def run_example() -> None:
    init_state: AgentState = {
        "user_input": "請幫我查一下今天天氣怎樣，然後用一句話總結告訴我。",
        "history": [],
        "tool_result": None,
        "status": "thinking",
        "final_answer": None,
        "pending_tool_query": None,
    }
    final_state = graph.invoke(init_state)
    print("====== 最終答案 ======")
    print(final_state.get("final_answer", "(沒有答案)"))
    print("\n====== 完整 ReAct 過程 (history) ======")
    for step in final_state.get("history", []):
        print(step)


if __name__ == "__main__":
    run_example()
