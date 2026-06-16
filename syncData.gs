// 定義一個函數叫做 syncData，這是整個程式的主程式
function syncData() {
  
  // ========== 第1步：取得試算表物件 ==========
  // SpreadsheetApp 是 Google Sheet 的全局物件
  // .getActiveSpreadsheet() 會拿到「目前打開的這個 Google Sheet 檔案」
  // 把它儲存在變數 ss 中，用來操作整個試算表
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  
  // 取得目前「正在顯示」的工作表（工作表 = 試算表內的分頁）
  // 如果有多個分頁（標籤），這會取得使用者目前在看的那一個
  // 假設按鈕放在目前這張對帳表上，直接取得當前活動的工作表
  var targetSheet = ss.getActiveSheet(); 
  
  // 用 getSheetByName() 方法，根據工作表的「名稱」找出指定的工作表
  // 這裡要找的是名叫 '訂貨明細' 的工作表
  // 如果找到，就把它存在變數 sourceSheet；如果找不到，會回傳 null
  var sourceSheet = ss.getSheetByName('訂貨明細');
  
  // ========== 檢查工作表是否存在 ==========
  // 判斷 sourceSheet 是否為 null（找不到工作表的意思）
  // ! 符號代表「不是」，所以 !sourceSheet 表示「如果沒有找到工作表」
  if (!sourceSheet) {
    // 如果工作表不存在，就彈出一個警告視窗給使用者看
    // SpreadsheetApp.getUi() 是用來顯示介面的物件
    // .alert() 方法會秀出一個對話框
    SpreadsheetApp.getUi().alert("找不到名為 '訂貨明細' 的工作表，請檢查名稱是否正確。");
    
    // return 會停止執行整個函數，不再往下執行
    return;
  }
  
  // ==========================================
  // 第2步：記錄目前已有的勾選狀態
  // ==========================================
  // 建立一個空的物件（像是一個箱子），用來儲存所有已勾選的資料
  // 這樣做是為了待會更新資料時，能保留使用者之前的勾選狀態
  var existingStates = {};
  
  // targetSheet.getLastRow() 會找到工作表中「最後一行有資料的列號」
  // 例如：如果有資料到第 10 列，就會回傳 10
  // 把這個列號存在變數 targetLastRow
  var targetLastRow = targetSheet.getLastRow();
  
  // 檢查是否至少有 2 列
  // 因為第 1 列通常是標題列，所以如果有資料，應該要從第 2 列開始
  if (targetLastRow >= 2) {
    
    // ========== 讀取資料 ==========
    // .getRange(起始列, 起始欄, 要讀多少列, 要讀多少欄) 會定位到一個矩形範圍
    // getRange(2, 1, targetLastRow - 1, 4) 的意思是：
    //   - 從第 2 列開始
    //   - 從第 1 欄開始
    //   - 讀取 (targetLastRow - 1) 列（也就是除了標題列外的所有列）
    //   - 讀取 4 欄（A、B、C、D 四欄）
    // .getValues() 會把這些儲存格的「值」（數字、字串、布林值等）讀成陣列
    // 返回結果是一個二維陣列，例如 [[值1, 值2, 值3, 值4], [值1, 值2, 值3, 值4], ...]
    var targetValues = targetSheet.getRange(2, 1, targetLastRow - 1, 4).getValues();
    
    // .getDisplayValues() 和 getValues() 很像，但會取得「顯示的格式」
    // 例如：如果儲存格存的是日期物件，getValues() 拿到的可能是亂碼，
    //      但 getDisplayValues() 會拿到格式化後的字串（像是「2025/12」）
    // 這裡只讀前 2 欄（月份和廠商），因為只需要比對這兩欄
    var targetDisplayValues = targetSheet.getRange(2, 1, targetLastRow - 1, 2).getDisplayValues();
    
    // ========== 逐列處理資料 ==========
    // 開始一個迴圈，從第 0 個元素遍歷到最後一個元素
    // i++ 表示每次迴圈後，i 加 1
    for (var i = 0; i < targetValues.length; i++) {
      
      // 取得第 i 列的第 0 個元素（也就是第 1 欄，A 欄的月份）
      // .trim() 是一個字串函數，會移除前後的空白
      var monthStr = targetDisplayValues[i][0].trim();
      
      // 取得第 i 列的第 1 個元素（也就是第 2 欄，B 欄的廠商名稱）
      // .trim() 同樣會移除前後空白
      var vendorStr = targetDisplayValues[i][1].trim();
      
      // 只有當月份和廠商都不是空白時，才記錄這筆資料
      // !== 表示「不等於」
      if (monthStr !== "" && vendorStr !== "") {
        
        // 建立一個唯一的 Key，用來識別這筆資料
        // 例如：「2025/12_廠商A」
        // 用 + 符號把兩個字串連接起來，中間加上 _ 分隔符號
        var key = monthStr + "_" + vendorStr;
        
        // 把這筆資料的勾選狀態存進去
        // targetValues[i][2] 是第 C 欄（第 3 個元素），存的是勾選狀態（true 或 false）
        // targetValues[i][3] 是第 D 欄（第 4 個元素），存的也是勾選狀態
        // === true 是在檢查「是否為 true」，結果也會是 true 或 false
        // 這樣做可以確保一定是布林值
        existingStates[key] = {
          checked1: targetValues[i][2] === true,  // C欄：是否已對帳（第 3 欄）
          checked2: targetValues[i][3] === true   // D欄：是否已付款（第 4 欄）
        };
      }
    }
  }
  
  // ==========================================
  // 第3步：從源工作表讀取原始資料
  // ==========================================
  // .getLastRow() 找出 '訂貨明細' 工作表中最後一行有資料的列號
  var sourceLastRow = sourceSheet.getLastRow();
  
  // 檢查源工作表是否真的有資料（至少要有 2 列，包含標題列）
  if (sourceLastRow < 2) {
    // 如果沒有資料，顯示警告訊息，然後停止
    SpreadsheetApp.getUi().alert("'訂貨明細' 內沒有發現任何資料。");
    return;
  }
  
  // ========== 讀取特定的兩欄 ==========
  // 欄 B（第 2 欄）存放的是「付款月份」
  // getRange(2, 2, sourceLastRow - 1, 1) 的意思是：
  //   - 從第 2 列開始（跳過標題）
  //   - 從第 2 欄開始（B 欄）
  //   - 讀取 (sourceLastRow - 1) 列（除了標題外的所有列）
  //   - 讀取 1 欄（只讀 B 欄，不讀其他欄）
  // .getDisplayValues() 取得格式化後的值（確保日期格式正確）
  var colB = sourceSheet.getRange(2, 2, sourceLastRow - 1, 1).getDisplayValues(); 
  
  // 欄 F（第 6 欄）存放的是「廠商名稱」
  // getRange(2, 6, sourceLastRow - 1, 1) 的意思是：
  //   - 從第 2 列開始
  //   - 從第 6 欄開始（F 欄）
  //   - 讀取 (sourceLastRow - 1) 列
  //   - 讀取 1 欄
  var colF = sourceSheet.getRange(2, 6, sourceLastRow - 1, 1).getDisplayValues(); 
  
  // ==========================================
  // 第4步：去除重複值（UNIQUE 邏輯）
  // ==========================================
  // 建立一個空的物件，用來存放「不重複」的組合
  // 物件的 Key 會自動排除重複項
  var uniqueMap = {};
  
  // 遍歷 colB 陣列中的每一個元素
  // colB.length 是陣列有多少個元素
  for (var j = 0; j < colB.length; j++) {
    
    // 取得第 j 列的月份
    // colB[j] 是陣列中的第 j 個元素（是一個陣列，因為 getDisplayValues 回傳二維陣列）
    // colB[j][0] 是這個陣列的第 0 個元素（唯一的一個值，因為我們只讀了 1 欄）
    var month = colB[j][0].trim();
    
    // 取得第 j 列的廠商名稱
    var vendor = colF[j][0].trim();
    
    // 只有當月份不是空白時，才處理這筆資料
    // 相當於試算表公式中的過濾條件 '訂貨明細'!B2:B <> ""
    if (month !== "") {
      // 建立唯一的 Key，格式是「月份_廠商」
      var uniqueKey = month + "_" + vendor;
      
      // 把這筆資料放入 uniqueMap 物件
      // 如果相同的 Key 出現過，新的會覆蓋舊的
      // 這就是去除重複的方式
      uniqueMap[uniqueKey] = [month, vendor];
    }
  }
  
  // ========== 將物件轉回陣列 ==========
  // 建立一個空陣列，用來存放轉換後的資料
  var uniqueRows = [];
  
  // for...in 迴圈會遍歷物件中的每一個 Key
  for (var key in uniqueMap) {
    // 把每個值（[month, vendor] 陣列）加入到 uniqueRows 陣列中
    // .push() 方法會把元素加到陣列的最後面
    uniqueRows.push(uniqueMap[key]);
  }
  
  // ==========================================
  // 第5步：排序資料（依月份由小到大）
  // ==========================================
  // .sort() 是陣列的排序方法
  // 裡面放一個「比較函數」，用來決定怎麼排序
  // 函數會收到兩個相鄰的元素 a 和 b，並回傳一個數字：
  //   - 負數：a 排在 b 前面
  //   - 0：a 和 b 相等，位置不變
  //   - 正數：b 排在 a 前面
  uniqueRows.sort(function(a, b) {
    
    // a[0] 是第一筆資料的月份（例如「2025/12」）
    // b[0] 是第二筆資料的月份
    // .split('/') 會用 / 符號把字串分開，回傳陣列
    // 例如「2025/12」會變成 ['2025', '12']
    var partsA = a[0].split('/');
    var partsB = b[0].split('/');
    
    // 檢查是否成功分割成 2 個部分（年份和月份）
    // 如果都成功，就用數字排序；否則用字串排序
    if (partsA.length === 2 && partsB.length === 2) {
      
      // .parseInt(字串, 10) 會把字串轉成整數
      // 第二個參數 10 表示以十進制解析
      // 例如 parseInt('2025', 10) 會變成 2025（數字）
      var yA = parseInt(partsA[0], 10);  // 第一筆的年份轉成整數
      var mA = parseInt(partsA[1], 10);  // 第一筆的月份轉成整數
      var yB = parseInt(partsB[0], 10);  // 第二筆的年份轉成整數
      var mB = parseInt(partsB[1], 10);  // 第二筆的月份轉成整數
      
      // 先比較年份
      // yA - yB 會得到一個數字：
      //   - 如果 yA > yB，結果是正數，表示 b 排在前面（年份小排前面）
      //   - 如果 yA < yB，結果是負數，表示 a 排在前面
      //   - 如果 yA === yB，結果是 0，表示年份相同，再看下一行
      if (yA !== yB) return yA - yB;
      
      // 如果年份相同，再比較月份
      // mA - mB 的邏輯同上
      if (mA !== mB) return mA - mB;
    }
    
    // 如果分割失敗（或其他異常情況），就用字串排序
    // .localeCompare() 是字串排序方法，會按照語言習慣排序
    // 例如「2025/01」會排在「2025/12」前面
    return a[0].localeCompare(b[0]);
  });
  
  // ==========================================
  // 第6步：組合最終要寫入的資料
  // ==========================================
  // 建立一個空陣列，用來存放最終的資料
  var finalData = [];
  
  // 遍歷排序好的 uniqueRows 陣列
  for (var k = 0; k < uniqueRows.length; k++) {
    
    // 取得第 k 筆資料的月份
    var m = uniqueRows[k][0];
    
    // 取得第 k 筆資料的廠商
    var v = uniqueRows[k][1];
    
    // 組成查詢用的 Key，用來在 existingStates 中尋找舊的勾選狀態
    var lookupKey = m + "_" + v;
    
    // 初始化兩個勾選狀態為 false（沒有勾選）
    var c1 = false;
    var c2 = false;
    
    // ========== 恢復舊的勾選狀態 ==========
    // 檢查在 existingStates 中是否有這個 Key 的資料
    // 如果有，表示使用者之前勾選過，現在要把狀態恢復回去
    if (existingStates[lookupKey]) {
      // 把舊的勾選狀態取出來
      c1 = existingStates[lookupKey].checked1;  // 恢復第 C 欄的狀態
      c2 = existingStates[lookupKey].checked2;  // 恢復第 D 欄的狀態
    }
    
    // 把這筆資料（月份、廠商、勾選狀態1、勾選狀態2）作為一個陣列加入 finalData
    // .push() 會把這個新陣列加到 finalData 的最後面
    finalData.push([m, v, c1, c2]);
  }
  
  // ==========================================
  // 第7步：清除舊資料並寫入新資料
  // ==========================================
  // 檢查目標工作表中是否至少有 2 列（標題列 + 資料列）
  if (targetLastRow >= 2) {
    
    // .getRange(起始列, 起始欄, 列數, 欄數) 定位到一個範圍
    // getRange(2, 1, targetLastRow - 1, 4) 的意思是：
    //   - 從第 2 列開始
    //   - 從第 1 欄開始
    //   - 選擇 (targetLastRow - 1) 列（除了標題外的所有列）
    //   - 選擇 4 欄（A、B、C、D）
    // .clearContent() 會清空這個範圍內的所有內容（但保留格式、核取方塊等）
    // 這和 .clear() 不同，.clear() 會連格式一起刪掉
    targetSheet.getRange(2, 1, targetLastRow - 1, 4).clearContent();
  }
  
  // ========== 寫入新資料 ==========
  // 檢查 finalData 是否有資料
  // .length 會回傳陣列有多少個元素
  if (finalData.length > 0) {
    
    // 定位到要寫入的範圍
    // getRange(2, 1, finalData.length, 4) 的意思是：
    //   - 從第 2 列開始
    //   - 從第 1 欄開始
    //   - 寫入 finalData.length 列（有幾筆資料，就寫幾列）
    //   - 寫入 4 欄（A、B、C、D）
    // .setValues(finalData) 會把二維陣列寫入到試算表中
    // 例如 finalData = [['2025/12', '廠商A', true, false], ['2025/01', '廠商B', false, true]]
    // 就會寫成兩列
    targetSheet.getRange(2, 1, finalData.length, 4).setValues(finalData);
    
    // .toast() 方法會在試算表的右下角顯示一個短暫的通知訊息
    // 第 1 個參數是訊息內容
    // 第 2 個參數是訊息的標題
    // 第 3 個參數是顯示秒數（3 秒後會自動消失）
    ss.toast("資料已成功重新同步，並精準對齊核取方塊！", "同步成功", 3);
    
  } else {
    // 如果沒有資料要寫入，就顯示另一個通知
    ss.toast("未發現有效資料。", "系統通知", 3);
  }
}
