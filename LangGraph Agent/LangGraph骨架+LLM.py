"""LangGraph 骨架 + LLM 版本（可直接執行）。"""

from __future__ import annotations

import json
from typing import Optional, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph


class OrderState(TypedDict):
    user_input: str
    drink: Optional[str]
    sugar: Optional[str]
    ice: Optional[str]
    available: Optional[bool]
    result: Optional[str]


MENU = ["珍珠奶茶", "紅茶拿鐵", "綠茶"]
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def parse_order(state: OrderState) -> OrderState:
    prompt = (
        "你是飲料店點單助手。"
        "請把使用者輸入解析成 JSON，鍵必須只有 drink、sugar、ice。"
        "若 drink 無法判斷請給 null；sugar 與 ice 若沒提到，預設 '正常'。"
        "只輸出 JSON，不要任何額外文字。"
    )
    response = llm.invoke(
        [
            SystemMessage(content=prompt),
            HumanMessage(content=state["user_input"]),
        ]
    )
    raw = getattr(response, "content", "")
    drink, sugar, ice = None, "正常", "正常"
    try:
        parsed = json.loads(raw)
        drink = parsed.get("drink")
        sugar = parsed.get("sugar") or "正常"
        ice = parsed.get("ice") or "正常"
    except Exception:
        # LLM 回傳格式不穩時，退回最小規則避免流程中斷。
        text = state["user_input"]
        if "珍珠奶茶" in text:
            drink = "珍珠奶茶"
        elif "紅茶拿鐵" in text:
            drink = "紅茶拿鐵"
        elif "綠茶" in text:
            drink = "綠茶"
        sugar = "半糖" if "半糖" in text else "正常"
        ice = "少冰" if "少冰" in text else "正常"
    return {**state, "drink": drink, "sugar": sugar, "ice": ice}


def check_menu(state: OrderState) -> OrderState:
    drink = state["drink"]
    available = drink in MENU if drink else False
    return {**state, "available": available}


def place_order(state: OrderState) -> OrderState:
    result = f"已為您點了一杯 {state['sugar']}、{state['ice']} 的 {state['drink']}"
    return {**state, "result": result}


def out_of_stock(state: OrderState) -> OrderState:
    return {**state, "result": f"很抱歉，目前沒有 {state['drink'] or '這個品項'}"}


def route_after_check(state: OrderState) -> str:
    return "place_order" if state["available"] else "out_of_stock"


builder = StateGraph(OrderState)
builder.add_node("parse_order", parse_order)
builder.add_node("check_menu", check_menu)
builder.add_node("place_order", place_order)
builder.add_node("out_of_stock", out_of_stock)
builder.set_entry_point("parse_order")
builder.add_edge("parse_order", "check_menu")
builder.add_conditional_edges(
    "check_menu",
    route_after_check,
    {"place_order": "place_order", "out_of_stock": "out_of_stock"},
)
builder.add_edge("place_order", END)
builder.add_edge("out_of_stock", END)
graph = builder.compile()


def run_example() -> None:
    initial_state: OrderState = {
        "user_input": "我要一杯半糖少冰的珍珠奶茶",
        "drink": None,
        "sugar": None,
        "ice": None,
        "available": None,
        "result": None,
    }
    result_state = graph.invoke(initial_state)
    print(result_state["result"])


if __name__ == "__main__":
    run_example()

# ===== 原教學段落保留（註解區） =====
# 1) 原教學重點是「只替換 parse_order node 為 LLM 解析」，其餘 graph 結構不動。
# 2) parse_order 建議透過 prompt + JSON 輸出，解析出 drink/sugar/ice。
# 3) check_menu / place_order / out_of_stock / route_after_check 維持骨架設計。
# 4) StateGraph 與 conditional edges 的接法不變，只換 node 內部實作。
# 5) 這份檔案已依上述原教學方向整理為可直接執行版本。
