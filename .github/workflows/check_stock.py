def check_stock(symbol, x_days, y_percent):
    # 0. 判斷市場 & 時區 & 時段
    if symbol.endswith(".TW"):
        # 台股：台北時間，08:30 ~ 15:00
        tz = pytz.timezone("Asia/Taipei")
        now = datetime.now(tz)
        session_start = time(8, 30)
        session_end = time(15, 0)
        market_name = "台股"
    else:
        # 美股：紐約時間，08:30 ~ 17:00
        tz = pytz.timezone("America/New_York")
        now = datetime.now(tz)
        session_start = time(8, 30)
        session_end = time(17, 0)
        market_name = "美股"

    # 0-1. 先看現在時間是否在交易時段（粗篩）
    if not (session_start <= now.time() <= session_end):
        print(f"{symbol} ({market_name}) 非交易時段，跳過")
        return None

    # 0-2. 再用 1 分鐘 K 線確認是否真的有在跑（精細判斷）
    ticker = yf.Ticker(symbol)
    min_data = ticker.history(period="1d", interval="1m")

    if min_data.empty:
        print(f"{symbol}: 今日無 1 分鐘資料，可能尚未開盤或休市，跳過")
        return None

    # 取最後一筆 1 分鐘 K 線時間（index 通常已帶時區）
    last_bar_time = min_data.index[-1]

    # 確保 last_bar_time 也在同一時區（保險做法）
    if last_bar_time.tzinfo is None:
        last_bar_time = tz.localize(last_bar_time)
    else:
        last_bar_time = last_bar_time.astimezone(tz)

    # 跟現在時間比較差距（分鐘）
    diff_min = (now - last_bar_time).total_seconds() / 60.0
    is_recent = diff_min <= 3

    if not is_recent:
        print(f"{symbol}: 最後一筆 1 分鐘資料距今 {diff_min:.1f} 分鐘，視為未開盤，跳過")
        return None

    print(f"{symbol}: {market_name} 開盤中（1 分K 最新差 {diff_min:.1f} 分鐘）")

    # 1. 下載股票資料，取得最近 x_days+5 天的歷史收盤價
    data = yf.download(symbol, period=f"{x_days+5}d", progress=False, auto_adjust=False)

    # 2. 檢查資料量是否足夠
    if len(data) < x_days + 1:
        print(f"{symbol}: not enough data")
        return None

    # 3. 取得收盤價序列，計算今日與 x_days 前的收盤價
    print(data["Close"])
    today = float(data["Close"].iloc[-1].item())          # 今日收盤價
    past = float(data["Close"].iloc[-x_days].item())      # x_days 前收盤價
    print(f"{symbol} today: {today}, {x_days} days ago: {past}")

    # 4. 計算漲跌幅百分比
    drop = (today - past) / past * 100

    # 5. 判斷是否觸發警示，並印出結果
    alert = "ALERT" if drop <= -float(y_percent) else "not triggered"
    print(f"{symbol}: {drop:.2f}% in {x_days} days (threshold: {y_percent}%) - {alert}")

    # 6. 處理收盤價歷史資料，取最近 x_days 筆
    close_data = data["Close"].iloc[-x_days:]
    start_date = close_data.index[0].strftime("%m-%d")  # 起始日期
    end_date = close_data.index[-1].strftime("%m-%d")   # 結束日期

    # 7. 格式化收盤價歷史，一筆一個 row
    pairs = [
        (close_data.index[i].strftime("%m-%d"), float(close_data.iloc[i].item()))
        for i in range(len(close_data))
    ]
    rows = [f"{date}: {price:.2f}" for date, price in pairs]
    history_text = "\n".join(rows)

    # 8. 回傳 bubble dict 給 flex message
    return build_bubble(symbol, start_date, end_date, x_days, drop, y_percent, history_text)
