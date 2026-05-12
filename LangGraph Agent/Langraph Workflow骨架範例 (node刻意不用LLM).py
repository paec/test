"""LangGraph 骨架範例（node 刻意不用 LLM，可直接執行）。"""

from __future__ import annotations

from typing import Optional, TypedDict

from langgraph.graph import END, StateGraph


class OrderState(TypedDict):
    user_input: str
    drink: Optional[str]
    sugar: Optional[str]
    ice: Optional[str]
    available: Optional[bool]
    result: Optional[str]


MENU = ["珍珠奶茶", "紅茶拿鐵", "綠茶"]


def parse_order(state: OrderState) -> OrderState:
    text = state["user_input"]
    if "珍珠奶茶" in text:
        drink = "珍珠奶茶"
    elif "紅茶拿鐵" in text:
        drink = "紅茶拿鐵"
    elif "綠茶" in text:
        drink = "綠茶"
    else:
        drink = None
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
    result = graph.invoke(initial_state)
    print(result["result"])


if __name__ == "__main__":
    run_example()

# ===== 原教學段落保留（註解區） =====
# 1) 原教學主軸：把流程拆成 State、Node、Edge、Conditional Edge。
# 2) parse_order / check_menu / place_order / out_of_stock 各自單一職責。
# 3) route_after_check 決定流程分支，等價於一般 if/else 但更外顯。
# 4) compile 後可透過 graph.invoke(initial_state) 一次跑完整個流程。
# 5) Agent 不等於 LLM；這個版本刻意示範「不靠 LLM 也能做有狀態流程」。
