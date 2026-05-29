可以，下面我幫你整理成一份**實用版總結筆記**。  
我會用你現在在思考的軟體開發 / agent engineering 視角來寫。

> **一句話先總結**  
> **LLM (no agent)** = 單次/少量回合的模型呼叫  
> **Agent** = 有 loop、會用工具、會自己多步完成任務  
> **Multi-agent** = 多個 agent 分工協作，由 workflow / handoff / orchestrator 串起來

***

# 1) 三者本質差異

## A. LLM（no agent）

**定義**  
直接呼叫模型，讓模型回文字 / 結構化輸出 / 單次工具結果；你自己負責流程控制。OpenAI 把 Responses API 定位為「直接 model requests」；Anthropic 的 Messages API 則是直接 prompt model 的介面。

**特徵**

* 沒有完整 agent loop（至少不是你自己以外的人幫你包好） 
* 多輪上下文通常由你自己傳回去維持；Anthropic Messages API 明確是 stateless，要你每次送完整歷史。 
* 適合單步、明確、短任務。

**代表性工具 / 介面**

* OpenAI **Responses API**（直接 model requests）
* Anthropic **Messages API**（direct model prompting） 

**典型例子**

* 「幫我把會議紀錄摘要成 5 點」
* 「把需求轉成 JSON schema」
* 「根據這段 code 解釋 bug 成因」

***

## B. Agent（單 agent）

**定義**  
在 LLM 外面再包一層 **agent runtime**：  
會規劃、呼叫工具、讀工具結果、決定下一步、持續 loop，直到完成任務。OpenAI Agents SDK 明確把 agent 定義成會「plan、call tools、keep enough state 完成 multi-step work」；Anthropic Agent SDK也強調提供與 Claude Code 相同的 tools、agent loop、context management。

**特徵**

* 有內建 agent loop：tool invocation → result → 繼續推理。 
* 有基本 state / context 管理。Anthropic Agent SDK 明確寫「same tools, agent loop, and context management that power Claude Code」；OpenAI Agents SDK 則有 sessions / state / tracing。 
* 通常也內建常見工具（讀檔、改檔、跑指令、MCP/函數工具）。 

**代表性工具**

* **Claude Code**：官方 coding agent，可讀 repo、改檔、跑測試、寫 PR。
* **Claude Agent SDK**：把 Claude Code 的工具、agent loop、context 管理做成可程式化 SDK。
* **OpenAI Agents SDK**：code-first agent runtime，含 tools、handoffs、guardrails、sessions、tracing。

**典型例子**

* 「修掉 auth.py 的 bug，跑測試，直到全部 pass」
* 「分析整個 repo，改掉一個 feature 的實作，再補測試」
* 「抓資料 → 清洗 → 產報表 → 存檔」

***

## C. Multi-agent

**定義**  
把工作拆給**多個 agent**，每個 agent 有不同職責，再透過 graph / handoff / orchestrator 串起來。LangGraph 官方明確定位為 low-level orchestration / runtime，可建 single / multi-agent / hierarchical workflows；CrewAI 則直接定位為 multi-agent automation framework。 

**特徵**

* 真正有「角色分工」：planner / engineer / tester / reviewer。
* 任務交接可能靠 workflow、handoff、artifact，不只是同一 agent 自己想下一步。
* 適合長任務、跨角色任務、要可重試 / 可觀測 / 可回滾的流程。

**代表性工具**

* **LangGraph**：低階 orchestration framework，適合顯式 workflow / stateful agent systems。 
* **CrewAI**：強調 cre​​ws / flows / collaborative multi-agent automation。
* **OpenAI Agents SDK**：可用 handoffs / agents-as-tools 建 multi-agent workflows。 
* **Codex subagents**：Codex 可在你明確要求時 spawn specialized subagents 並平行執行。
* **Claude Code 的新動態 workflows / 後台多 agents** 也開始出現，但主要仍是產品內建 orchestration，而不是像 LangGraph 那樣由你完全顯式控制。

**典型例子**

* 「需求分析 agent → 架構 agent → coding agent → QA agent → deploy agent」
* 「同一個 PR 用 security / bugs / maintainability / test flakiness 四個 agent 平行 review」
* 「研究 agent 蒐集資料、writer agent 起草、editor agent 修稿」

***

# 2) 最實用比較表

| 面向   | LLM (no agent)    | Agent               | Multi-agent                       |
| ---- | ----------------- | ------------------- | --------------------------------- |
| 核心單位 | 一次模型呼叫            | 一個會 loop 的 agent    | 多個 agent + orchestration          |
| 誰控流程 | 你自己               | agent runtime 幫很多   | workflow / orchestrator           |
| 工具使用 | 可有，但通常你自己串        | 內建 / 半內建            | 每個 agent 各自用工具                    |
| 任務形態 | 單步 / 短任務          | 中等複雜、多步任務           | 長流程、跨角色、分工任務                      |
| 狀態管理 | 你自己管              | runtime 幫你管一部分      | graph / workflow / artifacts 明確管理 |
| 優點   | 最簡單、最省錢、最可控       | 好用、效率高、少重造輪子        | 最穩、最可拆分、最適合長流程                    |
| 缺點   | 長任務容易失焦、你要自己寫很多控制 | 黑盒程度較高、長任務仍可能 drift | 架構最複雜、成本較高                        |

***

# 3) 代表性工具怎麼放到這三類

## LLM（no agent）

* OpenAI **Responses API**：直接對模型發 request，也能做 structured output / tools，但本質仍可用作 direct model call。
* Anthropic **Messages API**：direct prompting；conversation state 需你自己傳回。

## Agent

* **Claude Code**：最典型的 coding agent。
* **Claude Agent SDK**：把 Claude Code 的 agent能力程式化。
* **OpenAI Agents SDK**：單 agent 也很適合，含 tools / sessions / guardrails / tracing。

## Multi-agent

* **LangGraph**：白盒 orchestration。 
* **OpenAI Agents SDK handoffs**：偏 code-first multi-agent。 
* **Codex subagents**：偏黑盒 / 半黑盒 subagents。 

***

# 4) 什麼場景適合用哪一種？

## 適合 LLM（no agent）

如果你要的是：

* 問答
* summarization
* extract / classify / rewrite
* 一次就能完成的小任務

**典型場景**

* 規格轉 Markdown
* 文案改寫
* 單次 code explanation

***

## 適合 Agent

如果你要的是：

* 一個人可以從頭做完的多步任務
* 會用工具（檔案、shell、web、MCP）
* 想少寫很多 orchestration 邏輯

**典型場景**

* 修 bug + 補測試
* 做 repo refactor
* 自動收集資料後產出報告

***

## 適合 Multi-agent

如果你要的是：

* 任務很長、容易失焦
* 要角色分工
* 要可重試 / 可觀測 / 可 checkpoint
* 要 artifact handoff（例如 `REQUIREMENT.md -> architecture.md -> code -> test_report.json`）

**典型場景**

* 完整軟體交付流程
* 複雜研究工作流
* 多角色審查 / 平行 review

***

# 5) 一個很實用的判斷口訣

## 用 LLM（no agent）

> **只是要答案，不是要它自己做事**

## 用 Agent

> **要它自己做事，但還像是一個人能做完的任務**

## 用 Multi-agent

> **任務太長 / 太複雜，必須拆角色與流程**

***

# 6) 對你目前架構的對應

你現在想的「 軟體開發交付週期 」 (含需求分析、規格、實作、測試、部署) 

* **LangGraph 當主 workflow**
* 底下接多個 sub-agent
* coding 主要用 **Claude Code CLI**

這個明確屬於：

> **Multi-agent（白盒 orchestration）**

而不是單純 Agent。  
LangGraph 負責 **流程 / state / handoff**；Claude Code 負責 **執行型 coding agent**。LangGraph 本身官方就主打 single / multi-agent / hierarchical workflows；Claude Code 則是 agentic coding system。 

***

# 7) 最後一句超濃縮版

> **LLM = 問模型**  
> **Agent = 給模型工具與 loop，讓它自己做事**  
> **Multi-agent = 把事情拆給多個 agent，靠 workflow 協作完成**

***

