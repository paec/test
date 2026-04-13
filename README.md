- 在終端機ctrl I 也可以打開copilot?
  * 值接在repo案 鍵盤 "."，會打開github.dev，這是本地瀏覽器版vs code但基本沒什麼功能只是類似文字編輯器
  * 用github codespaces (用github的算力)，點擊綠色的 「Code」 按鈕 -> 「Codespaces」 -> 「Create codespace on master」。
     * 可以安裝 gituhb copilot

- 在Github可以打開網頁版VS?


---
2026/4/13

- Issues可以當作repo的工作單?
- 先用Plan模式讓AI生成修改計畫.md ，再用agent模式開始依照規格書實作，效果通常比較好?
- PlayWright寫前端測試 (類似cypress，但playwright是直接用python語法寫，cypress是js/ts)


- MCP
   - MCP 模式流程：Copilot ➔ (本地) ➔ 你電腦上的 MCP Server (小程序) ➔ (網路/本地) ➔ 真實服務 (GitHub API / 本地資料庫)。+
   - MCP 運作全流程：從模型決策到工具執行
1. 啟動與掛載：你在 mcp.json 配置 Server 套件後，VS Code 會在本地啟動 MCP Server 程序，並透過 list_tools 握手協議獲取一份標準化的「工具清單」。
2. 注入意圖：VS Code 將清單中的工具描述轉化為文字，注入 Prompt 餵給 模型 (LLM)，使其具備調用外部能力的意識。
3. 模型下令 (Tool Call)：當模型判斷需要使用工具時，會輸出一段「工具調用意圖（包含函數名與參數）」。
4. Host 轉譯 (封裝 Input)：VS Code 截獲模型的意圖後，將其整理成符合 MCP 規範的 JSON RPC Input，透過標準通訊管道（STDIO）丟給 本地 MCP Server。
5. 代為執行：本地 MCP Server 接收到標準 Input 後，解析參數並代為操作 雲端 API 或 地端資源（如資料庫、檔案系統）。
6. 結果回填 (任務閉環)：MCP Server 將工具執行的原始 Output 整理成 MCP 規範的 JSON 格式 傳回；由 VS Code 將其包裝成新的 Context Prompt 餵回給模型，完成具備即時數據能力的任務閉環。
        
- conext7
- 
