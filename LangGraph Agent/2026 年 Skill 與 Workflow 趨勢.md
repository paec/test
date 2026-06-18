# 2026 年 Skill 與 Workflow 趨勢筆記

## 1. 核心趨勢：從「拉死流程」走向「Agent + Skill + Workflow 混合架構」

2026 年的趨勢不是 **Skill 取代 Workflow**，而是：

> **Skill 負責讓 AI 理解 SOP、規則、工具使用方式；Workflow 負責控制流程、權限、驗證、審計與落地執行。**

OpenAI Codex Skills 與 Anthropic Claude Agent Skills 都已經把 Skill 視為一種可重用的任務能力包，通常包含 `SKILL.md`、metadata、instructions、scripts、references 等內容，讓 Agent 在需要時載入並執行特定任務流程。 [\[developers...openai.com\]](https://developers.openai.com/codex/skills), [\[platform.claude.com\]](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)

***

## 2. Skill.md 的角色

可以把 `SKILL.md` 理解成：

```text
Agent 的 SOP / 操作手冊 / 任務規範
```

它通常會描述：

* 什麼情境下要使用這個 Skill
* 任務執行步驟
* 工具/API 怎麼呼叫
* 輸入輸出格式
* 錯誤處理原則
* 範例與注意事項

現在主流設計是 **Progressive Disclosure**：一開始只載入 Skill 的名稱、描述、路徑，等模型判斷任務需要時，才讀入完整 `SKILL.md`，避免一開始就塞爆 context。 [\[developers...openai.com\]](https://developers.openai.com/codex/skills), [\[platform.claude.com\]](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)

***

## 3. Workflow 的角色

Workflow 不會消失，而是從「每個步驟都硬拉節點」變成「負責治理與保底」。

Workflow 適合處理：

* Trigger 觸發
* 權限檢查
* 資料前處理
* Schema validation
* IF / ELSE 硬性規則
* Human approval
* Log / audit trail
* Transaction commit / rollback
* API 實際送出與結果確認

n8n 的 production AI 思路也偏向把 AI 放進 deterministic workflow 裡：workflow 控制 AI 收到什麼資料、能用什麼工具、輸出怎麼驗證，以及後續如何路由。 [\[blog.n8n.io\]](https://blog.n8n.io/production-ai-playbook-introduction/)

***

## 4. 推薦架構

比較成熟的做法是：

```text
Workflow Trigger
  ↓
Deterministic Node：權限 / 輸入檢查
  ↓
Agent + SKILL.md：判斷、整理、推理、選工具
  ↓
Deterministic Node：Schema 驗證
  ↓
Deterministic Node：商業規則檢查
  ↓
Human Approval：必要時人工審批
  ↓
Deterministic Node：正式寫入 / 發送 / 執行
  ↓
Log / Audit
```

簡單講：

```text
SKILL.md 讓 AI 知道「應該怎麼做」
Workflow 保證系統「只能安全地做」
```

***

## 5. 哪些適合交給 Skill？

適合 Skill / Agent 處理的任務：

* 文件整理、摘要、分類
* 報表生成
* 複雜文字判斷
* API 呼叫順序判斷
* 根據情境選擇工具
* 資料清洗建議
* 跨系統資訊彙整
* 非高風險的彈性商務流程

例如：

```text
根據客戶資料判斷是否需要補件
根據錯誤訊息推論可能原因
依照公司格式整理週報
依 API 回傳內容決定下一步查詢
```

***

## 6. 哪些必須用 Workflow / Code 保底？

以下不應只靠 `SKILL.md`：

* 付款、薪資、財務對帳
* 金額門檻判斷
* 權限控管
* 審批流程
* 資料庫寫入
* transaction commit / rollback
* API 最終送出
* schema validation
* 法規或稽核要求
* 高頻大量資料處理
* 製造業安全控制

例如：

```text
金額 > 100,000 必須主管簽核
API 回傳 status != success 必須中止
JSON schema validation 失敗不得落庫
付款前必須確認銀行帳號與簽核狀態
```

這些要用 deterministic node / 程式碼 / workflow engine 固定住。

***

## 7. 重要注意事項

### A. Skill 不是 System Prompt

`SKILL.md` 可以想成「被動態載入到高優先級 context 的 SOP」，但它不等於真正的 system prompt。不同平台實作會有差異。

### B. Skill 不是狀態機

模型會根據上下文推論「現在做到哪一步」，但它不是像程式一樣有絕對可靠的狀態 pointer。

所以重要流程不要只靠：

```text
模型應該記得現在做到 Step 3
```

更安全的是讓 workflow / database 保存狀態：

```text
current_step = "APPROVAL_PENDING"
```

### C. Context 很大不代表永遠可靠

即使 context window 很大，模型仍可能因為以下原因忽略規則：

* 指令太長
* 工具回傳太多
* 任務分支太複雜
* 多個 Skill 規則衝突
* 使用者後續要求干擾原流程
* 長任務中注意力分散

### D. 結構化輸出仍要驗證

JSON Mode / Function Calling 已經很強，但正式系統仍應做：

* schema validation
* required field check
* enum 檢查
* 金額 / 日期 / ID 格式檢查
* retry / fallback
* error handling

不要假設模型輸出永遠 100% 正確。

***

## 8. 實務判斷原則

可以用這個標準判斷：

```text
可錯、可重試、偏判斷 → Skill / Agent
不可錯、要審計、要保證 → Workflow / Code
```

更簡化：

| 類型     | 建議               |
| ------ | ---------------- |
| 彈性判斷   | Skill            |
| SOP 說明 | Skill            |
| 工具選擇   | Skill            |
| 權限檢查   | Workflow / Code  |
| 最終送出   | Workflow / Code  |
| 財務/付款  | Workflow / Code  |
| 輸出格式驗證 | Workflow / Code  |
| 高風險決策  | Human + Workflow |

***

## 9. 一句話總結

> **2026 的主流不是「Workflow 被 Skill 取代」，而是「Skill 讓 Agent 變聰明，Workflow 讓 Agent 變安全可控」。**

最佳架構是：

```text
Skill = AI 的操作手冊
Agent = 會判斷的執行者
Tool Calling = AI 的手腳
Workflow = 流程骨架與安全護欄
Code / DB = 最終可靠狀態與規則來源
```
