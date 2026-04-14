

下面直接在你原本的「手刻規則版骨架」上，**只換掉 parse_order 這個 node，改成用 LLM 解析**。其他 graph / edge / state 結構都不動，讓你清楚看到「怎麼裝上大腦」。

我先假設你用的是 langchain-openai + langgraph，Python 環境大致如下：

```bash

pip install langchain-openai langgraph

# 也可能還有 langchain, pydantic 等，看你專案

```

並在環境變數中放好 OPENAI_API_KEY。

---

## 1. State 不用改（維持你原本的骨架）

```python

from typing import TypedDict

class OrderState(TypedDict):

    user_input: str

    drink: str | None

    sugar: str | None

    ice: str | None

    available: bool | None

    result: str | None

```

---

## 2. 新版 parse_order：改用 LLM 解析

### 2-1 初始化 LLM

用 LangChain 的 ChatOpenAI（你可替換成任何 LangChain 支援的 model，例如 gpt-4.1 / gpt-4o 等）：

```python

from langchain_openai import ChatOpenAI

from langchain_core.prompts import ChatPromptTemplate

from langchain_core.output_parsers import JsonOutputParser

llm = ChatOpenAI(

    model="gpt-4o-mini",   # 或你想用的 model

    temperature=0

)

```

### 2-2 設計一個「輸出 JSON」的 prompt

我們希望 LLM 回傳一個 JSON，剛好對應到你 OrderState 裡要填的欄位drink, sugar, ice。

```python

order_prompt = ChatPromptTemplate.from_messages(

    [

        (

            "system",

            """你是一個飲料店點單助手。請根據使用者輸入，解析出「飲料品項、糖度、冰塊」。

請只輸出 JSON，不要多說任何話。

規則：

- drink：字串，例如 "珍珠奶茶"、"紅茶拿鐵"、"綠茶"。如果看不出來，就給 null。

- sugar：字串，例如 "無糖"、"微糖"、"半糖"、"少糖"、"正常"。如果沒說，就預設 "正常"。

- ice：字串，例如 "去冰"、"微冰"、"少冰"、"正常"、"熱"。如果沒說，就預設 "正常"。

"""

        ),

        ("user", "{user_input}")

    ]

)

parser = JsonOutputParser()

order_chain = order_prompt | llm | parser

```

> 這條 order_chain 就是：  

> 使用者輸入 → 填進 prompt → 丟給 LLM → 把回傳字串 parse 成 Python dict。

### 2-3 用這條 chain 改寫 parse_order

```python

def parse_order(state: OrderState) -> OrderState:

    user_input = state["user_input"]

    # 呼叫 LLM chain 解析

    parsed = order_chain.invoke({"user_input": user_input})

    # parsed 期待長這樣：

    # {

    #   "drink": "珍珠奶茶",

    #   "sugar": "半糖",

    #   "ice": "少冰"

    # }

    drink = parsed.get("drink")

    sugar = parsed.get("sugar") or "正常"

    ice = parsed.get("ice") or "正常"

    return {

        **state,

        "drink": drink,

        "sugar": sugar,

        "ice": ice,

    }

```

到這裡你就已經「裝上大腦」了：  

原本是 if "珍珠奶茶" in text: ... 的硬寫規則，現在改成叫 LLM 幫你判斷。

---

## 3. 其他 node 完全不動

check_menu / place_order / out_of_stock / routing / edge 都可以用你原來那套：

```python

MENU = ["珍珠奶茶", "紅茶拿鐵", "綠茶"]

def check_menu(state: OrderState) -> OrderState:

    drink = state["drink"]

    available = drink in MENU if drink else False

    return {**state, "available": available}

def place_order(state: OrderState) -> OrderState:

    result = f"已為您點了一杯 {state['sugar']}、{state['ice']} 的 {state['drink']}"

    return {**state, "result": result}

def out_of_stock(state: OrderState) -> OrderState:

    return {

        **state,

        "result": f"很抱歉，目前沒有 {state['drink'] or '這個品項'}"

    }

def route_after_check(state: OrderState):

    return "place_order" if state["available"] else "out_of_stock"

```

---

## 4. Graph 定義也都不用改，只是 node 的實作變了

```python

from langgraph.graph import StateGraph, END

builder = StateGraph(OrderState)

# 這裡的 parse_order 已經是「用 LLM 的版本」

builder.add_node("parse_order", parse_order)

builder.add_node("check_menu", check_menu)

builder.add_node("place_order", place_order)

builder.add_node("out_of_stock", out_of_stock)

builder.set_entry_point("parse_order")

builder.add_edge("parse_order", "check_menu")

builder.add_conditional_edges(

    "check_menu",

    route_after_check,

    {

        "place_order": "place_order",

        "out_of_stock": "out_of_stock",

    },

)

builder.add_edge("place_order", END)

builder.add_edge("out_of_stock", END)

graph = builder.compile()

```

---

## 5. 實際跑一次（和你原本骨架完全同介面）

```python

initial_state = {

    "user_input": "我要一杯半糖少冰的珍珠奶茶",

    "drink": None,

    "sugar": None,

    "ice": None,

    "available": None,

    "result": None,

}

result_state = graph.invoke(initial_state)

print(result_state["result"])

# 例：已為您點了一杯 半糖、少冰 的 珍珠奶茶

```

---

## 6. 這樣就達成你要的「原本刻意隱藏 LLM，現在裝上大腦」

關鍵點：

- State / graph 結構完全沒變：  

  你仍然是 OrderState + 4 個 node + edge / conditional edge。

- 只換 node 的實作：  

  parse_order 從「字串規則」換成「LLM chain」，其他 node 不必知道這件事。

- 之後你想再加更多 LLM 能力（例如：  

  - out_of_stock 裡多問「要不要改點 A / B / C？」  

  - 加一個 suggest_alternative node 讓 LLM 幫你推薦替代品  

  ）也可以用同樣方式：**新增 node，接上 edge**。

如果你貼出你目前實際的檔案結構 / 套件版本（langchain / langgraph / openai），我可以幫你調成「可直接貼進你專案就能跑」的最小完整範例。
