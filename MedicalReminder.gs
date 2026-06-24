/**
 * 主要執行函式：檢查慢箋日期並發送 LINE 輪播(Carousel)通知
 */
function checkAndSendReminders() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName("慢箋");
  
  if (!sheet) {
    console.log("錯誤：找不到名為 '慢箋' 的工作表！");
    return;
  }
  
  // 取得工作表內所有資料
  const data = sheet.getDataRange().getValues();
  if (data.length <= 1) {
    console.log("工作表內無足夠資料（僅有標題或為空）。");
    return;
  }
  
  // 1. 取得今日台灣時間物件（將時分秒歸零，只比對純日期）
  const tzTodayStr = Utilities.formatDate(new Date(), "GMT+8", "yyyy/M/d");
  const todayParts = tzTodayStr.split("/");
  const currentYear = parseInt(todayParts[0], 10);
  const todayMidnight = new Date(currentYear, parseInt(todayParts[1], 10) - 1, parseInt(todayParts[2], 10));
  
  console.log(`[系統通知] 開始執行排程，今日台灣日期為: ${tzTodayStr}`);
  
  // 欄位對應索引
  const NAME_IDX = 2;
  
  // 【新欄位設定】定義要檢查的期數、日期欄位與對應的狀態欄位
  // 註：這裡預設第二期狀態在索引 4 (欄位 E)、第三期狀態在索引 6 (欄位 G)，可依實際試算表結構調整 statusIdx
  const phaseConfigs = [
    { dateIdx: 3, statusIdx: 4, label: "第二期" },
    { dateIdx: 5, statusIdx: 6, label: "第三期" }
  ];
  
  // 建立一個陣列，用來收集所有符合條件的病患卡片 (bubbles)
  let patientBubbles = [];
  
  // 從第二列 (i=1) 開始巡覽（跳過標題列）
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    const name = row[NAME_IDX] ? row[NAME_IDX].toString().trim() : "";
    
    // 防呆：若姓名為空則跳過
    if (!name) continue;
    
    // 依序檢查第二期與第三期
    for (const config of phaseConfigs) {
      const medicineRange = row[config.dateIdx] ? row[config.dateIdx].toString().trim() : "";
      const actualPickupDate = row[config.statusIdx] ? row[config.statusIdx].toString().trim() : "";
      
      // 防呆：若領藥日期區間為空，或者不含波浪號 '~' 則跳過
      if (!medicineRange || !medicineRange.includes("~")) continue;
      
      // 擷取起始日期 (例如 "6/24~7/1" 切出 "6/24")
      const startDateStr = medicineRange.split("~")[0].trim();
      
      // 2. 將轉出來的起始日期（如 6/24）也轉成 Date 物件
      const startParts = startDateStr.split("/");
      if (startParts.length !== 2) continue; 
      const startDateMidnight = new Date(currentYear, parseInt(startParts[0], 10) - 1, parseInt(startParts[1], 10));
      
      // 判斷條件：台灣時間 >= 起始日期 且尚未領藥
      if (todayMidnight >= startDateMidnight && (actualPickupDate === "" || actualPickupDate === "X")) {
        console.log(`➔ 發現符合通知對象！第 ${i+1} 列: ${name} (${config.label})`);
        
        // 產生單張卡片物件（傳入對應的期數文字）
        const singleBubble = getMedicationFlexTemplate(name, medicineRange, config.label);
        
        // 先把卡片塞進陣列，先不急著發送
        patientBubbles.push(singleBubble);
      }
    }
  }
  
  const totalMatches = patientBubbles.length;
  console.log(`[系統通知] 檢查完畢，今日符合通知總人數：${totalMatches} 人`);
  
  // 3. 開始打包成 Carousel 並發送
  if (totalMatches > 0) {
    // LINE 規定一個 Carousel 最多只能塞 12 張卡片，所以我們用迴圈每 12 張切一包發送
    while (patientBubbles.length > 0) {
      const chunk = patientBubbles.splice(0, 12); // 每次取出最多 12 張卡片
      
      // 包裝成 LINE Carousel 格式
      const carouselPayload = {
        "type": "carousel",
        "contents": chunk
      };
      
      // 呼叫發送功能（整包送出，群組只會跳一個通知！）
      sendLine(carouselPayload, `今日慢箋領藥通知 (共 ${totalMatches} 筆)`);
    }
    console.log(`[系統通知] 輪播訊息發送成功。`);
  } else {
    console.log(`[系統通知] 今日無人符合通知條件，不發送訊息。`);
  }
}

===
/**
 * 設計慢籤領藥提醒的 LINE Flex Message 物件
 * @param {string} name - 病患姓名
 * @param {string} rangeText - 領藥區間 (如 "6/24~7/1")
 * @param {string} phaseLabel - 期數文字 (如 "第二期" 或 "第三期")
 * @return {Object} Flex Message 的 bubble 內容
 */
function getMedicationFlexTemplate(name, rangeText, phaseLabel) {
  return {
    "type": "bubble",
    "size": "mega",
    "header": {
      "type": "box",
      "layout": "vertical",
      "backgroundColor": "#0C6243", // 採用沉穩專業的醫療深綠色
      "paddingAll": "xl",
      "contents": [
        {
          "type": "text",
          "text": "📋 慢性處方箋 · 領藥提醒",
          "color": "#FFFFFF",
          "weight": "bold",
          "size": "lg"
        },
        {
          "type": "text",
          "text": "提醒您今日起可前往健保藥局領藥",
          "color": "#A3E2C9",
          "size": "xs",
          "margin": "xs"
        }
      ]
    },
    "body": {
      "type": "box",
      "layout": "vertical",
      "spacing": "md",
      "paddingAll": "xl",
      "contents": [
        {
          "type": "text",
          "text": `親愛的民眾您好：\n您的${phaseLabel}慢性病連續處方箋已達可領藥起始日，請抽空前往領取藥品。`,
          "size": "sm",
          "color": "#555555",
          "wrap": true,
          "lineSpacing": "4px"
        },
        {
          "type": "separator",
          "margin": "lg"
        },
        {
          "type": "box",
          "layout": "vertical",
          "margin": "md",
          "spacing": "sm",
          "contents": [
            {
              "type": "box",
              "layout": "horizontal",
              "contents": [
                { "type": "text", "text": "患者姓名", "color": "#888888", "size": "sm", "flex": 2 },
                { "type": "text", "text": name, "color": "#222222", "size": "sm", "weight": "bold", "flex": 5 }
              ]
            },
            {
              "type": "box",
              "layout": "horizontal",
              "contents": [
                { "type": "text", "text": "領藥期程", "color": "#888888", "size": "sm", "flex": 2 },
                { "type": "text", "text": rangeText, "color": "#D9383A", "size": "sm", "weight": "bold", "flex": 5 }
              ]
            },
            {
              "type": "box",
              "layout": "horizontal",
              "contents": [
                { "type": "text", "text": "目前狀態", "color": "#888888", "size": "sm", "flex": 2 },
                { "type": "text", "text": "⏳ 今日起開放領藥", "color": "#0C6243", "size": "sm", "weight": "bold", "flex": 5 }
              ]
            }
          ]
        },
        {
          "type": "separator",
          "margin": "lg"
        },
        // 貼心提醒區塊
        {
          "type": "box",
          "layout": "vertical",
          "backgroundColor": "#F4F9F6",
          "paddingAll": "md",
          "cornerRadius": "sm",
          "contents": [
            {
              "type": "text",
              "text": "💡 領藥小叮嚀",
              "color": "#0C6243",
              "size": "xs",
              "weight": "bold"
            },
            {
              "type": "text",
              "text": `1. 請務必攜帶「健保卡」與「${phaseLabel}慢籤憑證」。\n2. 可至原開立醫療院所或附近健保特約藥局領取。\n3. 若您近日已完成領藥，請忽略此通知。`,
              "color": "#666666",
              "size": "xs",
              "wrap": true,
              "margin": "xs",
              "lineSpacing": "3px"
            }
          ]
        }
      ]
    }
  };
}
