---
description: 進入虛擬環境並啟動應用程式
---

# 啟動 Canto-Beats 應用程式

這個 workflow 會引導你進入虛擬環境並啟動 Canto-Beats 應用程式。

## 步驟

### 1. 切換到項目目錄

首先，確保你在正確的項目目錄中：

```bash
cd /Users/user/Downloads/Canto-Beats-Apps-main
```

### 2. 檢查虛擬環境是否存在

確認 `venv` 目錄存在：

```bash
ls -la venv
```

如果虛擬環境不存在，需要先創建：

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-macos-silicon.txt
```

### 3. 激活虛擬環境

// turbo
```bash
source venv/bin/activate
```

激活後，你的終端提示符前面應該會出現 `(venv)` 標記。

### 4. 驗證 Python 環境

檢查 Python 版本和虛擬環境路徑：

// turbo
```bash
which python
python --version
```

### 5. 檢查關鍵依賴（可選）

驗證主要依賴是否已安裝：

// turbo
```bash
python -c "import PySide6; print('✅ PySide6:', PySide6.__version__)"
python -c "import mlx; print('✅ MLX:', mlx.__version__)"
python -c "import torch; print('✅ PyTorch:', torch.__version__)"
```

### 6. 啟動應用程式

// turbo
```bash
python main.py
```

應用程式會顯示啟動畫面（splash screen），然後載入主視窗。

## 使用快捷腳本（推薦）

項目已經提供了一個便捷的啟動腳本 `run_app.sh`，它會自動執行上述所有步驟：

// turbo
```bash
./run_app.sh
```

如果腳本沒有執行權限，先賦予權限：

```bash
chmod +x run_app.sh
./run_app.sh
```

## 退出虛擬環境

當你完成工作後，可以退出虛擬環境：

```bash
deactivate
```

## 故障排除

### 問題：找不到 venv 目錄

**解決方案**：創建新的虛擬環境

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-macos-silicon.txt
```

### 問題：依賴缺失

**解決方案**：重新安裝依賴

```bash
source venv/bin/activate
pip install -r requirements-macos-silicon.txt
```

### 問題：MLX 相關錯誤

**解決方案**：確保使用正確的 MLX 版本（針對 Apple Silicon）

```bash
source venv/bin/activate
pip install mlx==0.20.0 mlx-lm==0.19.3
```

### 問題：權限錯誤

**解決方案**：確保腳本有執行權限

```bash
chmod +x run_app.sh
chmod +x main.py
```

## 注意事項

1. **Apple Silicon 專用**：此項目針對 macOS Apple Silicon（M1/M2/M3）優化，使用 MLX 框架進行 GPU 加速。

2. **依賴檢查**：首次運行前，確保所有依賴都已正確安裝。可以運行 `check_env.py` 進行完整的環境檢查。

3. **GPU 狀態**：應用程式啟動時會自動檢測 GPU 狀態（Apple Metal/CUDA/CPU），並在終端顯示相關信息。

4. **虛擬環境隔離**：始終在虛擬環境中運行應用程式，避免與系統 Python 環境衝突。
