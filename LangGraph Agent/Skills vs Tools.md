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
