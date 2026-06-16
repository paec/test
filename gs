function syncData() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  // 假設按鈕放在目前這張對帳表上，直接取得當前活動的工作表
  var targetSheet = ss.getActiveSheet(); 
  var sourceSheet = ss.getSheetByName('訂貨明細');
  
  if (!sourceSheet) {
    SpreadsheetApp.getUi().alert("找不到名為 '訂貨明細' 的工作表，請檢查名稱是否正確。");
    return;
  }
  
  // ==========================================
  // 1. 記錄目前畫面上已勾選的狀態
  // ==========================================
  var existingStates = {};
  var targetLastRow = targetSheet.getLastRow();
  
  if (targetLastRow >= 2) {
    // 讀取整張表的資料與勾選狀態
    var targetValues = targetSheet.getRange(2, 1, targetLastRow - 1, 4).getValues();
    // 使用 getDisplayValues 確保日期格式（如 2025/12）精準以字串比對
    var targetDisplayValues = targetSheet.getRange(2, 1, targetLastRow - 1, 2).getDisplayValues();
    
    for (var i = 0; i < targetValues.length; i++) {
      var monthStr = targetDisplayValues[i][0].trim();
      var vendorStr = targetDisplayValues[i][1].trim();
      
      if (monthStr !== "" && vendorStr !== "") {
        // 用「月份_廠商」建立唯一 Key
        var key = monthStr + "_" + vendorStr;
        existingStates[key] = {
          checked1: targetValues[i][2] === true, // C欄：是否已對帳
          checked2: targetValues[i][3] === true  // D欄：是否已付款
        };
      }
    }
  }
  
  // ==========================================
  // 2. 從 '訂貨明細' 撈取原始資料 (模擬 FILTER 邏輯)
  // ==========================================
  var sourceLastRow = sourceSheet.getLastRow();
  if (sourceLastRow < 2) {
    SpreadsheetApp.getUi().alert("'訂貨明細' 內沒有發現任何資料。");
    return;
  }
  
  // 欄 B (付款月份) 是第 2 欄，欄 F (廠商) 是第 6 欄
  var colB = sourceSheet.getRange(2, 2, sourceLastRow - 1, 1).getDisplayValues(); 
  var colF = sourceSheet.getRange(2, 6, sourceLastRow - 1, 1).getDisplayValues(); 
  
  // ==========================================
  // 3. 執行 UNIQUE 排除重複值
  // ==========================================
  var uniqueMap = {};
  for (var j = 0; j < colB.length; j++) {
    var month = colB[j][0].trim();
    var vendor = colF[j][0].trim();
    
    // 相當於 '訂貨明細'!B2:B <> ""
    if (month !== "") {
      var uniqueKey = month + "_" + vendor;
      uniqueMap[uniqueKey] = [month, vendor];
    }
  }
  
  // 將不重複物件轉回陣列
  var uniqueRows = [];
  for (var key in uniqueMap) {
    uniqueRows.push(uniqueMap[key]);
  }
  
  // ==========================================
  // 4. 執行 SORT 排序 (依據月份由小到大)
  // ==========================================
  uniqueRows.sort(function(a, b) {
    var partsA = a[0].split('/');
    var partsB = b[0].split('/');
    
    // 針對 YYYY/MM 格式進行正確的年份與月份數字排序
    if (partsA.length === 2 && partsB.length === 2) {
      var yA = parseInt(partsA[0], 10);
      var mA = parseInt(partsA[1], 10);
      var yB = parseInt(partsB[0], 10);
      var mB = parseInt(partsB[1], 10);
      
      if (yA !== yB) return yA - yB;
      if (mA !== mB) return mA - mB;
    }
    return a[0].localeCompare(b[0]); // 備用字串排序
  });
  
  // ==========================================
  // 5. 比對舊狀態，組合最終要寫入的資料
  // ==========================================
  var finalData = [];
  for (var k = 0; k < uniqueRows.length; k++) {
    var m = uniqueRows[k][0];
    var v = uniqueRows[k][1];
    var lookupKey = m + "_" + v;
    
    var c1 = false;
    var c2 = false;
    
    // 如果之前有記錄過這組月份+廠商的勾選狀態，就還原它
    if (existingStates[lookupKey]) {
      c1 = existingStates[lookupKey].checked1;
      c2 = existingStates[lookupKey].checked2;
    }
    
    finalData.push([m, v, c1, c2]);
  }
  
  // ==========================================
  // 6. 清除舊資料並寫入新資料
  // ==========================================
  // 先清除舊內容（clearContent 會保留核取方塊的設定，只清空值）
  if (targetLastRow >= 2) {
    targetSheet.getRange(2, 1, targetLastRow - 1, 4).clearContent();
  }
  
  // 寫入全新對齊後的資料
  if (finalData.length > 0) {
    targetSheet.getRange(2, 1, finalData.length, 4).setValues(finalData);
    ss.toast("資料已成功重新同步，並精準對齊核取方塊！", "同步成功", 3);
  } else {
    ss.toast("未發現有效資料。", "系統通知", 3);
  }
}
