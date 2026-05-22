# Claude Agent SDK — Skills vs Tools 筆記

## Tools 是什麼

Tools 是：

```text
Agent 可以執行的動作能力
```

例如：

*   Read
*   Grep
*   Bash
*   WebSearch
*   API call
*   DB query

Tools 本質上是：

```text
Function / Action Interface
```

通常會以：

```text
Tool Schema
```

形式提供給 LLM。

例如：

```json
{
  "name": "get_weather",
  "description": "Get weather by city",
  "parameters": {
    "city": "string"
  }
}
```

LLM 透過 schema 決定：

*   要不要呼叫
*   如何呼叫
*   傳什麼參數

***

# Skills 是什麼

Skills 是：

```text
Agent 的工作方法與專業能力包
```

通常包含：

*   workflow
*   best practices
*   domain knowledge
*   reasoning strategy
*   constraints

Skill 比較偏：

```text
Behavior / Strategy Layer
```

而不是 action。

***

# Skills 通常怎麼進 Context

在 Claude Agent SDK 中：

```text
Skills 通常會被注入到 system prompt/context layer
```

例如：

```md
你是一個 code review expert。

流程：
1. 先閱讀 diff
2. 找 security issue
3. 執行測試
4. 提供 structured feedback
```

這類內容會影響：

*   reasoning
*   planning
*   tool usage strategy
*   output style

***

# Tools vs Skills 核心差異

| 項目 | Skills                  | Tools              |
| -- | ----------------------- | ------------------ |
| 本質 | 行為策略                    | 執行能力               |
| 類型 | Prompt / Workflow       | Function / Schema  |
| 位置 | System Prompt / Context | Tool Schema        |
| 作用 | 指導 agent 如何做事           | 讓 agent 執行動作       |
| 影響 | reasoning / planning    | action execution   |
| 例子 | code-review skill       | Read / Grep / Bash |

***

# Claude Agent SDK Runtime 概念

```text
User Request
    ↓
Skill Matching
    ↓
Load Skill Context
    ↓
Agent Reasoning
    ↓
Tool Calling
    ↓
Observation
    ↓
Loop
```

***

# 官方 Skills 特性

Claude Agent SDK Skills：

*   透過 filesystem discovery 自動發現
*   啟動時先只載入 metadata
*   被 trigger 才完整載入
*   Claude 根據 context 自主選擇 skill [\[cloud.tencent.com\]](https://cloud.tencent.com/developer/article/2669652), [\[pasqualepi...litteri.it\]](https://pasqualepillitteri.it/en/news/3095/claude-agent-sdk-vs-langgraph-vs-crewai-benchmark-2026-en)

***

# 一句話記憶

```text
Skills = Agent 的做事方法
Tools = Agent 的手腳
```

或：

```text
Skill 通常進 system prompt/context
Tool 通常以 tool schema 提供給 LLM
```

***

# 🧠 Agent Workflow 與 LLM 推理機制

## ✅ 核心流程

```text
Skill 注入 → 指導 workflow
Tool call → 執行步驟
Tool result → 更新 context
LLM → 推理下一步
```

***

## ❗關鍵觀念

LLM **不會真正追蹤 workflow 進度**，而是：

```text
根據當前 context 推測現在應該在哪個步驟
```

***

## ✅ 正確模型

LLM 並沒有：

```text
state machine / step counter
```

實際運作是：

```text
觀察 context → 預測下一個合理行動
```

***

## 🔄 運作機制拆解

### 1. Skill 注入（提供理想流程）

```text
1. grep code
2. 找 bug
3. 執行測試
4. 提供建議
```

→ 僅為指引（非強制流程）

***

### 2. LLM 推理當前步驟

```text
User: review repo
```

```text
推測 → 應該先做 step 1
```

→ 呼叫 tool

***

### 3. Tool result 注入

```text
grep → found auth.py line 52
```

***

### 4. 下一輪推理

Context 包含：

```text
- Skill workflow
- User request
- Tool result
```

LLM 推論：

```text
step 1 已完成 → 應進入 step 2
```

***

## 🧩 抽象模型

```text
Skill       = 理想流程
Tool result = 當前狀況
LLM         = 推理下一步
```

***

## ⚠️ 限制

由於沒有顯式狀態控制，可能出現：

*   跳步
*   重複步驟
*   順序錯誤
*   忽略步驟

***

## ✅ 若需要確定性流程

需引入：

```text
- State machine（如 LangGraph）
- explicit step 欄位
- structured planner
```

***

## ✅ 一句話總結

```text
LLM 並不追蹤 workflow 進度，
而是根據 context 動態推理「現在應該做什麼」。
```

