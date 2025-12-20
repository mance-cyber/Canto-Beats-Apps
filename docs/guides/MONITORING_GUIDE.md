# 📊 Canto-Beats 監控系統指南

## 概述

這份指南將幫助你設置完整的監控系統，包括：
- ✅ 授權序號庫存監控（剩餘 < 100 時自動警報）
- ✅ Stripe Webhook 失敗監控
- ✅ Firebase 效能監控
- ✅ 系統健康檢查

---

## 📋 監控系統架構

```
┌─────────────────────────────────────────────────────────┐
│                    監控系統架構                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Supabase Database                                       │
│  ├── Triggers (自動檢查庫存)                             │
│  ├── Webhooks (觸發警報 API)                             │
│  └── Views (統計查詢)                                     │
│                                                          │
│  API Endpoints                                           │
│  ├── /api/monitor/stats (庫存統計)                       │
│  ├── /api/monitor/health (系統健康)                      │
│  └── /api/monitor/license-alert (警報處理)               │
│                                                          │
│  Email Alerts                                            │
│  └── Gmail SMTP (發送警報郵件)                           │
│                                                          │
│  External Monitoring                                     │
│  ├── Firebase Metrics (效能監控)                         │
│  └── Stripe Dashboard (支付監控)                         │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 設置步驟

### 步驟 1: 設置 Supabase 監控

#### 1.1 執行監控 SQL

1. 登入 [Supabase Dashboard](https://supabase.com/dashboard)
2. 選擇項目: `evzxjipgrmswkeeqlals`
3. 進入 **SQL Editor**
4. 創建新查詢
5. 複製並執行 `supabase-monitoring.sql` 的內容

**這將創建**:
- ✅ `check_license_inventory()` 函數 - 自動檢查庫存
- ✅ 觸發器 - 當序號被使用時自動執行檢查
- ✅ `license_stats` 視圖 - 快速查看統計
- ✅ `alert_logs` 表 - 記錄所有警報事件

#### 1.2 驗證安裝

執行以下查詢確認設置成功：

```sql
-- 查看授權序號統計
SELECT * FROM license_stats;
```

**預期結果**:
```
total_licenses | used_licenses | available_licenses | usage_percentage
--------------|---------------|-------------------|------------------
1000          | 24            | 976               | 2.40
```

#### 1.3 設置 Database Webhook（可選但建議）

如果你想要在庫存低時自動觸發 HTTP 請求：

1. 在 Supabase Dashboard → **Database** → **Webhooks**
2. 點擊 **Create a new hook**
3. 配置：
   - **Name**: `low-license-webhook`
   - **Table**: `licenses`
   - **Events**: `UPDATE`
   - **Type**: `HTTP Request`
   - **Method**: `POST`
   - **URL**: `https://[你的域名].web.app/api/monitor/license-alert`
   - **HTTP Headers**:
     ```json
     {
       "Content-Type": "application/json"
     }
     ```

4. 點擊 **Create webhook**

現在每當授權序號被使用時，webhook 會自動檢查庫存並發送警報郵件（如果需要）。

---

### 步驟 2: 測試監控 API

#### 2.1 系統健康檢查

在瀏覽器或使用 curl 訪問：

```bash
curl https://[你的域名].web.app/api/monitor/health
```

**成功回應**:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-11T10:30:00.000Z",
  "services": {
    "database": "healthy",
    "stripe": "healthy",
    "email": "configured"
  },
  "environment": "production"
}
```

**狀態說明**:
- `healthy` - 所有系統正常
- `degraded` - 部分服務有錯誤
- `unhealthy` - 配置錯誤

#### 2.2 授權序號統計

```bash
curl https://[你的域名].web.app/api/monitor/stats
```

**成功回應**:
```json
{
  "licenses": {
    "total": 1000,
    "available": 976,
    "used": 24,
    "usageRate": "2.4%"
  },
  "purchases": {
    "total": 24,
    "last24h": 5,
    "last7days": 18
  },
  "alert": {
    "lowLicenses": false,
    "threshold": 100,
    "message": "License inventory healthy"
  },
  "timestamp": "2025-12-11T10:30:00.000Z"
}
```

#### 2.3 手動觸發警報檢查

```bash
curl -X POST https://[你的域名].web.app/api/monitor/license-alert
```

---

### 步驟 3: 設置 Stripe 監控

Stripe 自動提供 webhook 監控，無需額外配置。

#### 3.1 查看 Webhook 狀態

1. 登入 [Stripe Dashboard](https://dashboard.stripe.com/)
2. 進入 **Developers** → **Webhooks**
3. 點擊你的 endpoint
4. 查看 **Attempts** 標籤

**健康指標**:
- ✅ 成功率應保持 > 99%
- ✅ 平均響應時間 < 500ms
- ✅ 無連續失敗記錄

#### 3.2 Webhook 失敗警報

Stripe 會在以下情況自動發送電郵警報：
- Webhook 連續失敗 5 次
- Webhook endpoint 無法訪問
- 響應碼不是 2xx

**接收警報的電郵**: Stripe 帳戶擁有者的電郵

#### 3.3 測試 Webhook

```bash
# 使用 Stripe CLI
stripe listen --forward-to https://[你的域名].web.app/api/webhook/stripe
stripe trigger checkout.session.completed
```

或在 Stripe Dashboard:
1. Webhooks → [你的 endpoint]
2. 點擊 **Send test webhook**
3. 選擇 `checkout.session.completed`
4. 點擊 **Send test webhook**

---

### 步驟 4: Firebase 監控

Firebase App Hosting 自動提供監控功能。

#### 4.1 查看即時指標

1. [Firebase Console](https://console.firebase.google.com/)
2. 選擇項目
3. **App Hosting** → **Metrics**

**可用指標**:
- **Request Count** - 總請求數
- **Error Rate** - 錯誤率 (應 < 1%)
- **Response Time** - 響應時間
  - P50 (中位數) - 應 < 200ms
  - P95 - 應 < 500ms
  - P99 - 應 < 1000ms

#### 4.2 設置錯誤率警報

1. Firebase Console → **Alerts**
2. 點擊 **Create alert**
3. 配置：
   - **Metric**: Error rate
   - **Condition**: `> 5%`
   - **Duration**: `5 minutes`
   - **Notification channels**: 你的電郵
4. 點擊 **Save**

#### 4.3 設置延遲警報

1. 點擊 **Create alert**
2. 配置：
   - **Metric**: Response time (p95)
   - **Condition**: `> 1000ms`
   - **Duration**: `10 minutes`
   - **Notification channels**: 你的電郵
3. 點擊 **Save**

---

## 📈 日常監控操作

### 每日檢查 (建議自動化)

#### 查看授權序號庫存

在 Supabase SQL Editor 執行：

```sql
SELECT * FROM license_stats;
```

或訪問 API:
```bash
curl https://[你的域名].web.app/api/monitor/stats
```

#### 查看每日銷售

```sql
SELECT * FROM daily_purchase_stats LIMIT 7;
```

### 每週檢查

#### 查看警報記錄

```sql
SELECT
  alert_type,
  severity,
  message,
  created_at
FROM alert_logs
WHERE created_at > NOW() - INTERVAL '7 days'
ORDER BY created_at DESC;
```

#### 查看 Webhook 成功率

1. Stripe Dashboard → Webhooks
2. 查看成功率圖表
3. 確認 > 99%

---

## 🚨 警報觸發條件

### 自動警報

系統會在以下情況自動發送警報郵件到 `info@cantobeats.com`:

#### 1. 授權序號庫存不足
- **觸發條件**: 可用序號 < 100
- **觸發時機**: 當序號被標記為已使用時
- **警報內容**:
  - 當前可用數量
  - 警戒線閾值
  - 建議行動

#### 2. Stripe Webhook 失敗
- **觸發條件**: 連續失敗 5 次
- **發送者**: Stripe 自動發送
- **警報內容**:
  - 失敗次數
  - 錯誤訊息
  - Endpoint URL

#### 3. Firebase 錯誤率過高
- **觸發條件**: 錯誤率 > 5% 持續 5 分鐘
- **發送者**: Firebase 自動發送
- **警報內容**:
  - 當前錯誤率
  - 受影響的請求數
  - 錯誤類型分佈

---

## 📊 監控儀表板

### 創建簡單的監控頁面（可選）

你可以創建一個內部監控頁面來顯示所有指標：

**訪問**: `https://[你的域名].web.app/admin/dashboard`

（需要先創建此頁面，或直接使用 API）

### 推薦的第三方監控工具

如果需要更專業的監控：

1. **Uptime Monitoring**:
   - [UptimeRobot](https://uptimerobot.com/) - 免費監控網站可用性
   - 設置每 5 分鐘檢查 `/api/monitor/health`

2. **Log Management**:
   - Firebase Console 內建日誌查看
   - 或使用 [Logtail](https://logtail.com/)

3. **Error Tracking**:
   - [Sentry](https://sentry.io/) - 錯誤追蹤和監控

---

## 🔍 故障排查

### 問題 1: 未收到授權序號警報郵件

**可能原因**:
1. Gmail App Password 配置錯誤
2. Database Webhook 未設置
3. API endpoint 無法訪問

**排查步驟**:
```sql
-- 檢查是否有警報記錄
SELECT * FROM alert_logs
WHERE alert_type = 'low_license_inventory'
ORDER BY created_at DESC
LIMIT 5;
```

```bash
# 手動測試警報 API
curl -X POST https://[你的域名].web.app/api/monitor/license-alert
```

### 問題 2: /api/monitor/stats 返回 500

**可能原因**: Supabase 連接失敗

**排查步驟**:
```bash
# 檢查健康狀態
curl https://[你的域名].web.app/api/monitor/health

# 查看 Firebase 日誌
# Firebase Console → Logs → 搜索 "monitor"
```

### 問題 3: Stripe Webhook 失敗率高

**可能原因**:
1. 環境變數未設置
2. Webhook Secret 不匹配
3. Database 錯誤

**排查步驟**:
1. Stripe Dashboard → Webhooks → View attempts
2. 查看失敗請求的錯誤訊息
3. Firebase Console → Logs → 搜索 "webhook"

---

## 📞 警報聯絡資訊

所有警報郵件發送到: **info@cantobeats.com**

確保此信箱能正常接收郵件，並設置適當的過濾規則：

**建議 Gmail 過濾器**:
- 來自: `info@cantobeats.com`
- 主旨包含: `警報` 或 `Alert`
- 動作: 標記為重要、加星號

---

## ✅ 監控檢查清單

部署前確認：

- [ ] Supabase 監控 SQL 已執行
- [ ] `license_stats` 視圖可正常查詢
- [ ] `/api/monitor/health` 返回 healthy
- [ ] `/api/monitor/stats` 返回正確數據
- [ ] Database Webhook 已創建（可選）
- [ ] Stripe Webhook 成功率 > 99%
- [ ] Firebase 錯誤率警報已設置
- [ ] 測試警報郵件已收到
- [ ] 監控 API 已加入日常檢查流程

---

## 🎯 總結

你現在擁有完整的監控系統：

**自動監控** ✅
- 授權序號庫存 (自動警報)
- Stripe Webhook 狀態
- Firebase 效能指標

**手動檢查** 📊
- 每日查看 `/api/monitor/stats`
- 每週查看 Supabase 警報記錄
- 每週查看 Stripe Dashboard

**警報通知** 🚨
- 郵件自動發送到 info@cantobeats.com
- Firebase 錯誤警報
- Stripe 失敗警報

祝監控順利！📈
