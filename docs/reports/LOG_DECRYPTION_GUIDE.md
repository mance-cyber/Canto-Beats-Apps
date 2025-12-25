# 跨平台 Log 解密指南 (Mac Log -> Windows 解密)

如果你需要喺 **Windows** 機解密由 **Mac** 產生嘅 `.log.enc` 檔案，請跟住以下步驟操作：

### 準備工作
1. 確保你嘅 Windows 機已經安裝咗 **Python**。
2. 確保 Windows 嘅專案資料夾入面已經有最新嘅代碼（包含咗我們剛剛加入嘅 Master Key 邏輯）。
3. 喺 Windows 終端機 (PowerShell 或 CMD) 安裝必要組件：
   ```bash
   pip install cryptography
   ```

---

### 第一步：傳送檔案
將 Mac 上面嘅 `.log.enc` 檔案（路徑通常喺 `~/.canto-beats/logs/`）複製到 Windows 機上面。
*   假設你將佢擺喺 Windows 嘅 `C:\Temp\mac_log.log.enc`。

### 第二步：開啟終端機
喺 Windows 開啟 **PowerShell** 或者 **Command Prompt (CMD)**，然後導航到 Canto-Beats 嘅專案根目錄。
```powershell
cd C:\你的路徑\Canto-Beats-Apps
```

### 第三步：執行解密指令
行以下指令（利用 `src\utils\logger.py` 作為工具）：

**方法 A：直接喺螢幕顯示內容**
```bash
python src/utils/logger.py "C:\Temp\mac_log.log.enc"
```

**方法 B：輸出生成一個文字檔 (建議)**
```bash
python src/utils/logger.py "C:\Temp\mac_log.log.enc" -o "C:\Temp\decrypted_mac_log.txt"
```

---

### 疑難排解與原理
*   **點解得咗？** 因為我哋依家統一用咗 **Master Key**。解密腳本會首先試「 Windows 本機密鑰」（會失敗），然後自動切換去試「萬能密鑰」（會成功）。
*   **錯誤：ModuleNotFoundError**：請確保你係喺專案根目錄行指令，或者將 `src` 加入 `PYTHONPATH`。
*   **舊檔案問題**：如果個 Log 檔係喺 2024 年 12 月 20 日之前產生嘅，因為當時未有 Master Key 邏輯，依然係解密唔到嘅。
