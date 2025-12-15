# Supabase 序號驗證系統設置指南

## 1. 創建 Supabase 項目

1. 訪問 [Supabase](https://supabase.com/) 並登入
2. 點擊 **New Project**
3. 填寫項目信息：
   - **Name**: `canto-beats-licenses`
   - **Region**: 選擇靠近用戶的區域（如 Singapore）
   - **Database Password**: 設置強密碼並保存

## 2. 運行數據庫 Schema

1. 進入項目後，點擊左側 **SQL Editor**
2. 點擊 **New Query**
3. 複製 `supabase_schema.sql` 的內容並貼上
4. 點擊 **Run** 執行

## 3. 獲取 API 憑證

1. 點擊左側 **Settings** → **API**
2. 複製以下信息：
   - **URL**: `https://xxxxx.supabase.co`
   - **anon public**: `eyJhbGciOiJIUzI1NiIsInR5cCI...`

## 4. 配置客戶端

在 `license_manager_supabase.py` 中修改：

```python
SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_ANON_KEY = "your-anon-key"
```

或者設置環境變量：
```
set SUPABASE_URL=https://your-project-id.supabase.co
set SUPABASE_ANON_KEY=your-anon-key
```

## 5. 添加序號

在 Supabase Dashboard 中：
1. 點擊 **Table Editor** → **licenses**
2. 點擊 **Insert row**
3. 填寫：
   - `license_key`: 例如 `CANTO-BEATS-2024-XXXX`
   - `license_type`: `permanent`
   - `transfers_allowed`: `1`

## 6. 整合到主程式

修改 `src/core/license_manager.py`，使用新的 Supabase 版本：

```python
# 替換舊的 import
from core.license_manager_supabase import LicenseManager, LicenseInfo
```

---

## 功能說明

| 功能 | 說明 |
|-----|------|
| 每序號機器數 | 1 台 |
| 可轉移次數 | 1 次 |
| 離線緩存 | 3 天 |
| 轉移操作 | 舊機器自動解綁 |
