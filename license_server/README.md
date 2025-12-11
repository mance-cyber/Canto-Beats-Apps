# Canto-beats License Distribution Server

自動化序號分發系統 - 處理 Stripe 付款並自動發送授權序號

## 🚀 快速開始

### 1. 安裝依賴

```bash
cd license_server
pip install -r requirements.txt
```

### 2. 設置環境變數

複製 `.env.example` 為 `.env`：

```bash
cp .env.example .env
```

編輯 `.env` 填入你的配置：

- **Stripe API Key**: 從 Stripe Dashboard 獲取
- **Stripe Webhook Secret**: 創建 Webhook 後獲取
- **SendGrid API Key**: 從 SendGrid 獲取
- **Admin Password**: 設置管理員密碼

### 3. 啟動伺服器

```bash
python main.py
```

或使用 uvicorn：

```bash
uvicorn main:app --reload
```

伺服器將在 http://localhost:8000 啟動

## 📡 API 端點

### 公開端點

- `GET /` - 健康檢查
- `GET /health` - 詳細健康狀態
- `POST /webhook/stripe` - Stripe Webhook（由 Stripe 調用）

### 管理員端點（需要認證）

使用 Basic Auth：`admin:你的密碼`

- `GET /admin/licenses` - 查看所有授權
- `GET /admin/orders` - 查看所有訂單
- `GET /admin/stats` - 系統統計
- `POST /admin/generate-license` - 手動生成授權

#### 管理員 API 使用範例：

```bash
# 查看所有授權
curl -u admin:your_password http://localhost:8000/admin/licenses

# 手動生成授權
curl -X POST -u admin:your_password \
  "http://localhost:8000/admin/generate-license?customer_email=user@example.com&customer_name=John"

# 查看統計
curl -u admin:your_password http://localhost:8000/admin/stats
```

## ⚙️ Stripe 設置

### 1. 創建產品

在 Stripe Dashboard:
1. Products → Create Product
2. 名稱：Canto-beats 授權
3. 價格：HKD 299 (或你的定價)
4. 記下 Price ID

### 2. 設置 Webhook

1. Developers → Webhooks → Add Endpoint
2. Endpoint URL: `https://你的域名/webhook/stripe`
3. 選擇事件：
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
4. 記下 Webhook Secret

### 3. 測試模式

使用 Stripe CLI 進行本地測試：

```bash
# 安裝 Stripe CLI
# https://stripe.com/docs/stripe-cli

# 登入
stripe login

# 轉發 Webhook 到本地
stripe listen --forward-to localhost:8000/webhook/stripe

# 觸發測試事件
stripe trigger payment_intent.succeeded
```

## 📧 SendGrid 設置

1. 註冊 SendGrid 帳戶（免費版每天 100 封）
2. 創建 API Key：Settings → API Keys → Create API Key
3. 驗證發件人郵箱：Settings → Sender Authentication

## 🗄️ 數據庫

### SQLite（開發）

默認使用 SQLite，數據存儲在 `licenses.db`

### PostgreSQL（生產）

建議生產環境使用 PostgreSQL：

```env
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

## 🚢 部署

### Railway（推薦）

1. 註冊 Railway.app
2. 新建專案 → Deploy from GitHub
3. 添加環境變數
4. 自動部署

### Render

1. 註冊 Render.com
2. New Web Service → Connect Repository
3. 設置環境變數
4. Deploy

### 環境變數清單

生產環境必須設置：
- `STRIPE_API_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `SENDGRID_API_KEY`
- `ADMIN_PASSWORD`
- `DATABASE_URL` (如果使用 PostgreSQL)

## 🔒 安全注意事項

⚠️ **重要**：
- 不要將 `.env` 提交到 Git
- 使用強密碼作為 Admin Password
- 生產環境必須使用 HTTPS
- 定期更換 API Keys

## 📊 監控

查看系統狀態：

```bash
curl http://localhost:8000/health
```

查看統計（需認證）：

```bash
curl -u admin:password http://localhost:8000/admin/stats
```

## 🐛 故障排除

### Webhook 驗證失敗

- 檢查 `STRIPE_WEBHOOK_SECRET` 是否正確
- 確保使用正確的 Webhook endpoint

### Email 發送失敗

- 檢查 SendGrid API Key
- 確認發件人郵箱已驗證
- 查看 SendGrid Dashboard 的發送紀錄

### 數據庫錯誤

- 確認 `DATABASE_URL` 格式正確
- 檢查數據庫連接權限

## 📝 License

Copyright © 2024 Canto-beats
