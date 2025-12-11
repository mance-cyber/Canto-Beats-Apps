# Stripe Webhook + 自動發序號 設定指南

## 1. Supabase 設定

### 1.1 建立 Supabase 專案
1. 去 [supabase.com](https://supabase.com) 建立新專案
2. 記低 Project URL 同 Service Role Key（Settings → API）

### 1.2 建立資料表
1. 去 SQL Editor
2. 複製 `supabase-schema.sql` 內容並執行

### 1.3 新增序號
喺 Supabase Table Editor 或者用 SQL：

```sql
INSERT INTO licenses (license_key) VALUES
  ('CANTO-2024-0001-ABCD'),
  ('CANTO-2024-0002-EFGH'),
  ('CANTO-2024-0003-IJKL'),
  ('CANTO-2024-0004-MNOP'),
  ('CANTO-2024-0005-QRST');
```

建議格式：`CANTO-YYYY-XXXX-XXXX`（可以用 Excel 批量生成）

---

## 2. Gmail App Password 設定

### 2.1 啟用兩步驗證
1. 去 [Google Account](https://myaccount.google.com)
2. Security → 2-Step Verification → 啟用

### 2.2 建立 App Password
1. Security → 2-Step Verification → App passwords
2. 選擇 "Other (Custom name)" → 輸入 "Canto-Beats"
3. 複製生成嘅 16 位密碼（格式：xxxx xxxx xxxx xxxx）

---

## 3. Stripe Webhook 設定

### 3.1 喺 Stripe Dashboard 建立 Webhook
1. 去 [Stripe Dashboard](https://dashboard.stripe.com) → Developers → Webhooks
2. 點擊 "Add endpoint"
3. Endpoint URL: `https://your-domain.com/api/webhook/stripe`
4. 選擇 events: `checkout.session.completed`
5. 複製 Signing secret（whsec_xxx）

### 3.2 本地測試（可選）
用 Stripe CLI 測試：

```bash
# 安裝 Stripe CLI
brew install stripe/stripe-cli/stripe

# 登入
stripe login

# 轉發 webhook 到本地
stripe listen --forward-to localhost:3000/api/webhook/stripe

# 觸發測試 event
stripe trigger checkout.session.completed
```

---

## 4. 環境變數設定

建立 `.env.local` 檔案：

```env
# Stripe
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJxxx

# Gmail
GMAIL_USER=info@cantobeats.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
```

---

## 5. 部署注意事項

### Vercel
1. 喺 Vercel Dashboard → Settings → Environment Variables 加入所有變數
2. 部署後更新 Stripe Webhook URL 為正式域名

### 其他平台
確保環境變數正確設定

---

## 6. 測試流程

1. 用 Stripe Test Mode 完成一次購買
2. 檢查 Supabase：
   - `licenses` 表有冇將序號標記為 `is_used = true`
   - `purchases` 表有冇新記錄
3. 檢查有冇收到 email

---

## 7. 監控同維護

### 檢查剩餘序號數量
```sql
SELECT COUNT(*) FROM licenses WHERE is_used = FALSE;
```

### 查看購買記錄
```sql
SELECT * FROM purchases ORDER BY created_at DESC;
```

### 序號用完警告
當序號少於 10 個時，建議補充新序號。

---

## 常見問題

### Q: Webhook 收唔到？
- 檢查 Stripe Dashboard → Webhooks → 睇 event logs
- 確保 endpoint URL 正確
- 確保 STRIPE_WEBHOOK_SECRET 正確

### Q: Email 發唔到？
- 檢查 Gmail App Password 係咪正確
- 檢查有冇啟用兩步驗證
- 睇 console log 有冇 error

### Q: 序號重複發送？
- 系統有防重複機制，會檢查 session_id
- 如果 Stripe retry webhook，唔會重複發序號
