# 授權序號生成與管理指南

本指南說明如何為 Canto-beats 生成授權序號，適用於 Firespace Studio 或其他銷售平台的訂單履行。

## 1. 生成序號工具

專案根目錄下的 `generate_license.py` 是您的序號生成工具。

### 基本指令

在終端機 (Terminal) 執行：

```bash
# 生成 1 個永久授權 (預設)
python generate_license.py

# 生成 10 個永久授權並存檔
python generate_license.py --count 10 --output licenses_batch_01.txt

# 生成試用版序號 (7天有效)
python generate_license.py --trial --count 5
```

### 參數說明

- `--count N`: 一次生成的數量 (例如 10, 50, 100)
- `--output filename`: 輸出的檔案名稱
- `--trial`: 生成試用版序號 (不加此參數則為永久版)
- `--transfers N`: 允許的轉移機器次數 (預設為 1，建議付費版設為 3-5 次以免除售後麻煩)

## 2. 銷售流程建議 (Firespace Landing Page)

由於目前採用「離線認證」模式，建議流程如下：

1.  **預先生成庫存**：
    執行 `python generate_license.py --count 100 --output stock_20241206.txt` 生成一批序號。

2.  **配置自動發貨 (如果平台支持)**：
    如果 Firespace 或您的支付網關 (如 Stripe/Gumroad) 支持上傳序號列表進行自動發貨，將生成的序號列表上傳即可。

3.  **手動發貨 (替代方案)**：
    收到訂單通知後，從文件中複製一個未使用的序號，通過 Email 發送給客戶。

## 3. 客戶激活流程

請告知客戶：
1.  下載並安裝 Canto-beats。
2.  開啟程式，點擊左上角選單 `檔案` -> `授權管理`。
3.  貼上序號並點擊「激活」。
4.  激活成功後，即可離線使用所有功能。

## 4. 常見問題

**Q: 客戶換電腦怎麼辦？**
A: 我們的序號內建「轉移次數」限制。如果客戶在舊電腦無法解除綁定（例如電腦壞了），只要該序號還有剩餘的轉移次數，直接在新電腦輸入序號即可激活。

**Q: 客戶退款怎麼辦？**
A: 離線模式無法遠端撤銷序號。建議直接將該序號標記為「無效」並在未來的程式更新中加入黑名單 (Blacklist)，或者單純接受這是離線模式的成本。
