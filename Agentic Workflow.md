# 🧠 Agentic Workflow 觀念筆記

> 一句話總覽：  
> **Agentic workflow = 讓 LLM 不是只回答問題，而是能「為了目標反覆思考、採取行動、根據結果修正策略」的一套系統設計。**

> ✅ 一句話先定錨
> 實務上的 Agentic workflow 幾乎都是混合式：
> 它包含固定程式流程（deterministic code）、人工節點（HITL），以及 AI / agentic 節點。
    
✅ 好的 agent node 特徵

* 判斷「意圖 / 例外 / 無法枚舉的情境」
* 原本靠人或複雜商規處理
* 容許不完美，但能被修正 / 監控

❌ 不適合 agent 化的點

* 金額計算
* 權限判斷
* 狀態轉移
* 法規 / 契約性硬規則

##### 🧠 一個舊專案，考慮要不要轉成 LangGraph + agentic能力 
1. 舊專案流程是否有轉成workflow架構的必要?
2. 其中是否有功能，有必要透過agentic取代?

```
有 workflow 架構需求？
    ├── No  → 原架構就好，考慮 LangChain 簡化 LLM 呼叫
    └── Yes → LangGraph
                ├── 有 agentic 需求 → LangGraph + agent 節點
                └── 無 agentic 需求 → LangGraph 純 workflow
```
> 有 workflow 需求，即使沒有 agentic 需求，LangGraph 本身就值得導入，純粹作為 workflow 管理工具使用也合理
>
***

## 1️⃣ Agentic AI 與傳統 LLM 應用的本質差異

### 傳統 LLM（Reactive）

*   Input → Output
*   一次性推理
*   不保證目標完成

```text
User → Prompt → Answer（結束）
```

***

### Agentic AI（Goal-driven）

*   以「目標」為中心
*   多步推進
*   能重試、修正、規劃

```text
Goal
→ Reasoning
→ Action
→ Feedback
→ Adapt
→ …直到完成或放棄
```

✅ **關鍵轉變**：  
從「回答得好不好」→「事情有沒有完成」

***

### Agentic Workflow 的工程本質

> **「Agentic」描述的是節點的能力，不是整個系統的性質。**

### ✅ Agentic Workflow 的正確理解

*   我有一個 **workflow**（顯性流程）
*   工作流中大多數 node 是 **deterministic code**
*   其中某一個（或幾個）node 不是單次呼叫
*   而是：
    *   有目標
    *   會 ReAct（decision → action → feedback）
    *   會自我規劃 / 修正
*   它完成後，把結果交回給下一個 deterministic node


### ❌ 常見錯誤認知
*   Agentic workflow = 整個系統都是 AI agent
*   Agentic workflow = 把所有節點都換成 LLM

### ✅ 正確認知
*   Agentic workflow = workflow 中，有節點具備 agentic 能力
*   其他節點仍然可以是 deterministic code
*   Agent 節點完成任務後，結果交回給下一個節點
***

## 2️⃣ ReAct：所有 agent 的「最小心智單位」

### ReAct 是什麼？

**Reason + Act 的循環模式**

```text
Thought → Action → Observation → Thought → ...
```

### ReAct 解決了兩件事

1.  **純推理會幻覺** → 用工具蒐集真實訊號
2.  **純流程太僵硬** → 用推理即時調整下一步

### 在 2026 年的定位

*   ✅ **仍然是最重要的底層 loop**
*   ❌ **不是完整 agent 架構**

> 👉 ReAct 是 *cognitive motor*，不是 *control system*

***

## 3️⃣ 純 ReAct Agent 的能力邊界

### 適合：

*   短任務
*   工具數量少
*   探索型問題

### 限制：

*   長任務容易 **goal drift**
*   缺乏全局一致性
*   無法穩定 scale 到 production

👉 這正是為什麼出現 **Plan-and-Execute**

***

## 4️⃣ Plan-and-Execute：把「想清楚」與「做事情」分開

### 核心思想

> **不要讓同一個 loop 同時負責全局規劃與細節執行**

***

### 基本結構

```text
Planner（控制層）
  └─ 決定「做什麼、順序是什麼」

Executor（執行層）
  └─ 決定「怎麼做」
```

***

### 你已經掌握的關鍵點（而且是正確的）

✅ **Executor 幾乎一定是 ReAct loop**

```text
[Executor]
Thought: 我需要查 API
Action: call_api()
Observation: result
Thought: 下一步…
```

✅ **Planner 也使用 ReAct-like reasoning**

*   但層級更高
*   動作較少
*   重點在：
    *   是否要 replan
    *   現在進度是否偏離目標

***

### 一句工程化定義（很重要）

> **Plan-and-Execute 是一個分層控制架構：  
> Planner 負責全局決策，Executor 以 ReAct loop 推進實際行動。**

***

## 5️⃣ Memory：讓 agent 不會「每輪重生」

Agentic workflow 若沒有記憶，只是「會重試的聊天機器」

### 常見三層記憶

#### 🟡 短期記憶（Context）

*   當前對話
*   當前步驟的 ReAct 軌跡

***

#### 🟢 工作記憶（Working Memory）

*   任務狀態摘要
*   已完成 / 待完成 checklist
*   active hypotheses

```json
{
  "goal": "...",
  "completed_steps": [...],
  "pending_steps": [...],
  "current_state": "..."
}
```

***

#### 🔵 長期記憶（Long-term）

*   使用者偏好
*   過去任務經驗
*   反思結果（見下面）

***

## 6️⃣ Reflection / Critic：讓 agent「越做越好」

### 為什麼反思重要？

ReAct 只會一直嘗試，但不一定會學習。

***

### Reflexion 核心 loop

```text
Execute
→ Evaluate（成功？為何失敗？）
→ Reflection（抽象成規則）
→ 存入記憶
→ 未來任務引用
```

✅ 特點：

*   不更新模型權重
*   只用自然語言記憶

***

### Reflection 放在哪？

*   常見做法：
    *   **Executor 外層**
    *   或 **Planner 決策前**

👉 本質上是 **品質保證層（QA layer）**

***

## 7️⃣ Multi-Agent：當單一 agent 不夠用時

### 原則（非常重要）

> **能用單一 agent 解決的問題，不要用多 agent**

***

### 什麼時候該用？

*   需要不同專業能力
*   單一 context 裝不下
*   任務可明確分工

***

### 常見角色分工

```text
Planner Agent
Executor Agent(s)
Reviewer / Critic Agent
```

✅ 每個 agent **內部仍然是 ReAct / Plan-Execute**

***

## 8️⃣ 一張「完整 agentic workflow 心智圖（文字版）」

```text
Goal
 └─ Planner
     ├─ Create plan
     ├─ Monitor progress
     └─ Replan if needed
         ↓
     Executor (ReAct loop)
         Thought
         → Action (tool)
         → Observation
         → Thought
         ↓
     Result
         ↓
     Reflection / Critic
         ↓
     Memory update
```

***
