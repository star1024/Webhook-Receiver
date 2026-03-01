# Webhook Receiver + Event Log Demo

這是一個可直接本機 demo 的 webhook 接收器，提供：

- `POST /webhook` 接收 JSON payload
- `GET /api/events` 查詢目前 event log
- `POST /api/events/clear` 清空 event log
- `/` 瀏覽器頁面查看事件列表

本專案只使用 Python 標準函式庫，不需要額外安裝套件。

## 專案位置

```powershell
c:\Users\yang4\Desktop\vibe code 專案\Webhook Receiver
```

## 啟動方式

在專案目錄執行：

```powershell
python .\app.py
```

啟動後打開：

```text
http://127.0.0.1:8000
```

## 功能驗證

### 1. 健康檢查

```powershell
Invoke-RestMethod -Method GET `
  -Uri "http://127.0.0.1:8000/api/health"
```

預期會回傳類似：

```json
{
  "status": "ok",
  "events": 0,
  "timestamp": "2026-03-01T00:00:00+00:00"
}
```

### 2. 發送測試 webhook

```powershell
Invoke-RestMethod -Method POST `
  -Uri "http://127.0.0.1:8000/webhook" `
  -ContentType "application/json" `
  -Body '{"event":"order.created","orderId":12345,"source":"demo"}'
```

預期會回傳類似：

```json
{
  "message": "Webhook received",
  "event_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "received_at": "2026-03-01T00:00:00+00:00"
}
```

### 3. 查詢 event log

```powershell
Invoke-RestMethod -Method GET `
  -Uri "http://127.0.0.1:8000/api/events"
```

預期在 `events` 陣列中看到剛剛送出的 payload：

```json
{
  "event": "order.created",
  "orderId": 12345,
  "source": "demo"
}
```

### 4. 驗證前端頁面

打開首頁後確認：

- `Event Log` 會顯示新收到的事件
- 點 `Refresh` 可以重新抓最新資料
- 點 `Clear Log` 可以清空事件列表

### 5. 清空 event log

```powershell
Invoke-RestMethod -Method POST `
  -Uri "http://127.0.0.1:8000/api/events/clear"
```

之後重新整理首頁，應該會看到空的事件列表。

## API 一覽

### `POST /webhook`

接收 webhook payload。若 body 是合法 JSON，系統會解析並寫入 event log；若不是合法 JSON，系統會以 `raw_body` 形式保存原始內容。

### `GET /api/events`

回傳目前記錄的事件列表。

### `POST /api/events/clear`

清空目前所有事件。

### `GET /api/health`

回傳服務狀態與目前事件數量。

## 資料儲存

事件資料會：

- 存在記憶體中供前端即時讀取
- 同步寫入 `data/events.jsonl`

## 常見問題

### 為什麼 PowerShell 用 `curl` 會報錯？

因為在 PowerShell 中，`curl` 常常是 `Invoke-WebRequest` 的別名，不是一般的 curl。

建議用：

```powershell
curl.exe
```

或直接使用：

```powershell
Invoke-RestMethod
```

### 為什麼 event log 裡看到 `raw_body`？

這表示送到 `/webhook` 的內容不是合法 JSON，通常是 PowerShell 的引號跳脫寫錯。

請使用這種格式：

```powershell
Invoke-RestMethod -Method POST `
  -Uri "http://127.0.0.1:8000/webhook" `
  -ContentType "application/json" `
  -Body '{"event":"order.created","orderId":12345,"source":"demo"}'
```
