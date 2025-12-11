# 🚀 Canto-Beats 部署指南

## 📋 目錄
1. [Firebase App Hosting 環境變數設置](#firebase-環境變數設置)
2. [Supabase 配置](#supabase-配置)
3. [Stripe 配置](#stripe-配置)
4. [監控系統設置](#監控系統設置)
5. [最終測試](#最終測試)

---

## 1. Firebase 環境變數設置

### 步驟 1: 進入 Firebase Console

1. 打開 [Firebase Console](https://console.firebase.google.com/)
2. 選擇你的項目
3. 在左側菜單點擊 **App Hosting**
4. 選擇你的應用 (canto-beats)
5. 點擊 **Environment variables** 標籤

### 步驟 2: 添加環境變數

點擊 **Add variable** 按鈕，逐一添加以下變數：

#### 2.1 Stripe 配置
```
變數名稱: STRIPE_SECRET_KEY
值: sk_live_51Sb5mu1PQE2SxAng...（你的 Stripe Live Secret Key）
描述: Stripe Live Mode Secret Key
```

```
變數名稱: STRIPE_WEBHOOK_SECRET
值: whsec_...（從 Stripe Webhook 設置頁面獲取）
描述: Stripe Webhook Signing Secret
```

#### 2.2 Supabase 配置
```
變數名稱: SUPABASE_URL
值: https://evzxjipgrmswkeeqlals.supabase.co
描述: Supabase Project URL
```

```
變數名稱: SUPABASE_SERVICE_ROLE_KEY
值: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...（你的 Service Role Key）
描述: Supabase Service Role Key (Do NOT use anon key)
```

#### 2.3 Gmail 配置
```
變數名稱: GMAIL_USER
值: info@cantobeats.com
描述: Gmail address for sending license emails
```

```
變數名稱: GMAIL_APP_PASSWORD
值: west uder crwn noaa
描述: Gmail App Password (16 characters)
```

#### 2.4 環境配置
```
變數名稱: NODE_ENV
值: production
描述: Node environment
```

### 步驟 3: 重新部署

環境變數更改後，需要重新部署：

1. 在 Firebase Console 中點擊 **Redeploy** 按鈕
2. 或者，從本地推送新的 commit 觸發自動部署：
   ```bash
   git commit --allow-empty -m "Trigger redeploy for env vars"
   git push
   ```

### 步驟 4: 驗證環境變數

部署完成後，檢查日誌確認環境變數已正確加載：

1. 在 Firebase Console → App Hosting → Logs
2. 查找啟動日誌，確認沒有 "environment variables not configured" 錯誤

---

## 2. Supabase 配置

### 步驟 1: 確認 RLS 政策

1. 登入 [Supabase Dashboard](https://supabase.com/dashboard)
2. 選擇你的項目: `evzxjipgrmswkeeqlals`
3. 進入 **SQL Editor**
4. 執行以下檢查：

```sql
-- 檢查 RLS 是否已啟用
SELECT
  schemaname,
  tablename,
  rowsecurity as "RLS Enabled"
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('licenses', 'purchases');
```

**預期結果**:
```
tablename  | RLS Enabled
-----------|-------------
licenses   | true
purchases  | true
```

如果顯示 `false`，執行以下 SQL：

```sql
-- 啟用 RLS
ALTER TABLE licenses ENABLE ROW LEVEL SECURITY;
ALTER TABLE purchases ENABLE ROW LEVEL SECURITY;

-- 創建政策（只允許 service role 訪問）
DROP POLICY IF EXISTS "Service role only" ON licenses;
DROP POLICY IF EXISTS "Service role only" ON purchases;

CREATE POLICY "Service role only" ON licenses
  FOR ALL
  USING (auth.role() = 'service_role');

CREATE POLICY "Service role only" ON purchases
  FOR ALL
  USING (auth.role() = 'service_role');
```

### 步驟 2: 檢查授權序號數量

```sql
-- 查看授權序號統計
SELECT
  COUNT(*) FILTER (WHERE is_used = false) as "可用序號",
  COUNT(*) FILTER (WHERE is_used = true) as "已使用序號",
  COUNT(*) as "總序號"
FROM licenses;
```

**預期結果**: 應該看到約 976 個可用序號

### 步驟 3: 設置自動警報 (Database Webhook)

在 Supabase Dashboard 創建 Database Webhook：

1. 進入 **Database** → **Webhooks**
2. 點擊 **Create a new hook**
3. 配置：
   - **Name**: `low-license-alert`
   - **Table**: `licenses`
   - **Events**: `UPDATE`
   - **Type**: `HTTP Request`
   - **Method**: `POST`
   - **URL**: `https://[你的域名].web.app/api/monitor/license-alert`

webhook 處理器已在代碼中準備好（見下方）。

---

## 3. Stripe 配置

### 步驟 1: 更新 Webhook Endpoint

1. 登入 [Stripe Dashboard](https://dashboard.stripe.com/)
2. 進入 **Developers** → **Webhooks**
3. 找到你的 webhook endpoint
4. 點擊 **Update details**
5. 更新 **Endpoint URL**:
   ```
   https://[你的-firebase-domain].web.app/api/webhook/stripe
   ```

   例如: `https://canto-beats-xxxx.web.app/api/webhook/stripe`

6. 確認 **Events to send**:
   - ✅ `checkout.session.completed`

7. 點擊 **Update endpoint**

### 步驟 2: 獲取新的 Webhook Secret

1. 在 webhook 詳情頁面，點擊 **Signing secret** 旁的 **Reveal**
2. 複製 secret (格式: `whsec_...`)
3. 更新 Firebase 環境變數中的 `STRIPE_WEBHOOK_SECRET`

### 步驟 3: 啟用支付方式

1. 進入 **Settings** → **Payment methods**
2. 確認以下方式已啟用：
   - ✅ Cards (Visa, Mastercard, etc.)
   - ✅ Alipay
   - ✅ WeChat Pay

如未啟用，點擊 **Add payment method** 添加。

### 步驟 4: 測試 Webhook

使用 Stripe CLI 測試：

```bash
stripe listen --forward-to https://[你的域名].web.app/api/webhook/stripe
stripe trigger checkout.session.completed
```

或在 Stripe Dashboard → Webhooks → [你的 endpoint] → **Send test webhook**

---

## 4. 監控系統設置

### Firebase 監控

#### 自動監控 (已內建)

Firebase App Hosting 自動提供：
- ✅ 錯誤率監控
- ✅ 請求延遲監控
- ✅ 可用性監控

**查看監控數據**:
1. Firebase Console → App Hosting → Metrics
2. 查看：
   - Request count
   - Error rate
   - Response time (p50, p95, p99)

#### 設置警報

1. Firebase Console → Alerts
2. 點擊 **Create alert**
3. 配置：
   - **Metric**: Error rate
   - **Condition**: `> 5%`
   - **Notification**: 你的電郵

### Stripe 監控

**查看 Webhook 狀態**:
1. Stripe Dashboard → Developers → Webhooks
2. 點擊你的 endpoint
3. 查看 **Attempts** 標籤：
   - 成功率應保持 > 99%
   - 失敗的請求會自動重試

**設置失敗警報**:
- Stripe 會自動在 webhook 連續失敗時發送電郵通知
- 無需額外配置

### Supabase 監控

**授權序號用量追蹤**:

監控 API 已在代碼中準備好（見 `src/app/api/monitor/stats/route.ts`）

訪問: `https://[你的域名].web.app/api/monitor/stats`

返回:
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
    "threshold": 100
  }
}
```

---

## 5. 最終測試

### 完整購買流程測試

1. **訪問網站**:
   ```
   https://[你的域名].web.app
   ```

2. **點擊「立即購買」按鈕**

3. **在 Stripe Checkout 完成測試購買**:
   - 使用測試卡: `4242 4242 4242 4242`
   - 或使用真實卡進行小額測試 (然後退款)

4. **檢查電郵**:
   - 應在 1 分鐘內收到授權序號

5. **驗證數據庫**:
   - 登入 Supabase Dashboard
   - 檢查 `purchases` 表有新記錄
   - 檢查 `licenses` 表中該序號標記為已使用

6. **檢查日誌**:
   - Firebase Console → Logs
   - 應看到: "License assigned to [email]"

### 測試監控 API

```bash
# 測試統計 API
curl https://[你的域名].web.app/api/monitor/stats

# 測試健康檢查
curl https://[你的域名].web.app/api/monitor/health
```

---

## ✅ 部署檢查清單

在正式上線前，確認：

- [ ] Firebase 環境變數已全部設置
- [ ] Firebase 應用已重新部署
- [ ] Supabase RLS 政策已啟用
- [ ] Supabase 有足夠的授權序號 (> 100)
- [ ] Stripe Webhook URL 已更新為生產域名
- [ ] Stripe 支付方式已啟用 (Cards, Alipay, WeChat Pay)
- [ ] 測試購買流程成功
- [ ] 收到測試授權序號電郵
- [ ] 監控 API 正常運作
- [ ] Firebase Metrics 顯示正常

---

## 🆘 常見問題排查

### 問題 1: Webhook 返回 500 錯誤

**可能原因**: 環境變數未設置

**解決方法**:
1. 檢查 Firebase Console → Environment variables
2. 確認所有變數都已添加
3. 重新部署應用

### 問題 2: 未收到授權序號電郵

**可能原因**: Gmail App Password 錯誤

**解決方法**:
1. 重新生成 Gmail App Password
2. 更新 Firebase 環境變數中的 `GMAIL_APP_PASSWORD`
3. 重新部署

### 問題 3: Stripe Webhook 簽名驗證失敗

**可能原因**: Webhook Secret 不匹配

**解決方法**:
1. 從 Stripe Dashboard 獲取最新的 Signing Secret
2. 更新 Firebase 環境變數中的 `STRIPE_WEBHOOK_SECRET`
3. 重新部署

### 問題 4: 數據庫連接失敗

**可能原因**: Supabase Service Role Key 錯誤

**解決方法**:
1. 登入 Supabase Dashboard → Settings → API
2. 複製 `service_role` key（不是 `anon` key）
3. 更新 Firebase 環境變數中的 `SUPABASE_SERVICE_ROLE_KEY`
4. 重新部署

---

## 📞 需要協助？

如遇到任何問題：
1. 檢查 Firebase Console → Logs
2. 檢查 Stripe Dashboard → Webhooks → Attempts
3. 檢查 Supabase Dashboard → Logs

祝部署順利！🎉
