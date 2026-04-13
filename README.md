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
   - 你在 mcp.json 配置 Server 套件後，GitHub Copilot 會在本地啟動MCP Server並執行該程序以獲取「工具清單」，將功能說明注入 Prompt 讓模型決策；當模型發出 tool_call 時，由本地 MCP Server 接收參數並代為操作雲端或地端工具，最後將回傳結果餵回給模型，完成具備即時數據能力的任務閉環。
        
- conext7
- 
