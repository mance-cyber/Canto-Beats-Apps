# 🚨 Canto-Beats 故障排除指南

## 問題：應用程序崩潰或顯示「缺少依賴」錯誤

### ❌ **常見錯誤症狀**
- Splash screen 後崩潰
- 提示「MPV 未安裝」（但本應使用 AVPlayer）
- 提示缺少 PySide6、MLX 或其他模塊
- 應用程序無法啟動

### ✅ **根本原因**
**您沒有在虛擬環境中運行應用程序！**

當您直接運行 `python main.py` 或 `python3 main.py` 時，系統會使用全局 Python 環境，而不是項目的虛擬環境。全局環境中沒有安裝項目所需的依賴。

---

## 🔧 **解決方案**

### **方法 1：使用啟動腳本（推薦）**

```bash
# 在項目根目錄運行
./run_app.sh
```

這個腳本會：
1. ✅ 自動激活虛擬環境
2. ✅ 檢查所有依賴
3. ✅ 啟動應用程序
4. ✅ 退出時自動清理

---

### **方法 2：手動激活虛擬環境**

```bash
# 1. 切換到項目目錄
cd /Users/nicleung/Public/Canto-Beats-Apps

# 2. 激活虛擬環境
source venv/bin/activate

# 3. 驗證環境（應該看到 (venv) 前綴）
which python
# 應該顯示: /Users/nicleung/Public/Canto-Beats-Apps/venv/bin/python

# 4. 運行應用程序
python main.py

# 5. 退出虛擬環境（應用程序關閉後）
deactivate
```

---

### **方法 3：直接使用虛擬環境的 Python**

```bash
# 不激活虛擬環境，直接使用虛擬環境的 Python
/Users/nicleung/Public/Canto-Beats-Apps/venv/bin/python main.py
```

---

## 🔍 **如何檢查您是否在虛擬環境中**

### **檢查 1：命令提示符**
激活虛擬環境後，您應該看到：
```
(venv) nicleung@MacBook Canto-Beats-Apps %
```

### **檢查 2：Python 路徑**
```bash
which python
```
應該顯示：
```
/Users/nicleung/Public/Canto-Beats-Apps/venv/bin/python
```

**❌ 錯誤的輸出**（全局 Python）：
```
/opt/homebrew/bin/python3
```

### **檢查 3：已安裝的包**
```bash
pip list | grep PySide6
```
應該顯示：
```
PySide6                       6.10.1
```

---

## 📦 **虛擬環境說明**

項目有兩個虛擬環境：

1. **`venv`** (Python 3.11) - **主要開發環境** ⭐
   - 用於日常開發和運行
   - 包含所有必要依賴

2. **`venv_compat`** (Python 3.12) - 兼容性測試環境
   - 用於測試 macOS 12 兼容性
   - 一般不需要使用

**默認使用 `venv`！**

---

## 🐛 **常見問題**

### **Q: 為什麼會顯示「MPV 未安裝」？**
**A:** 因為您在全局 Python 環境中運行，沒有安裝 `python-mpv` 模塊。但實際上應用程序應該使用 AVPlayer（Apple 原生播放器），不需要 MPV。

### **Q: 我已經安裝了 MPV（brew install mpv），為什麼還報錯？**
**A:** `brew install mpv` 安裝的是 MPV 播放器和 libmpv 庫，但 Python 還需要 `python-mpv` 模塊。這個模塊只在虛擬環境中安裝。

### **Q: 如何重新安裝依賴？**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### **Q: 虛擬環境損壞了怎麼辦？**
```bash
# 刪除舊的虛擬環境
rm -rf venv

# 創建新的虛擬環境
python3.11 -m venv venv

# 激活並安裝依賴
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🎯 **最佳實踐**

### **✅ 正確的工作流程**
1. 打開 Terminal
2. 運行 `./run_app.sh`
3. 完成！

### **❌ 錯誤的工作流程**
1. 打開 Terminal
2. 直接運行 `python main.py` ← **這會導致問題！**

---

## 📝 **創建桌面快捷方式（可選）**

如果您想雙擊圖標啟動應用程序：

```bash
# 創建 .command 文件（macOS 可執行腳本）
cat > ~/Desktop/Canto-Beats.command << 'EOF'
#!/bin/bash
cd /Users/nicleung/Public/Canto-Beats-Apps
./run_app.sh
EOF

# 設置可執行權限
chmod +x ~/Desktop/Canto-Beats.command
```

現在您可以雙擊桌面上的 `Canto-Beats.command` 啟動應用程序！

---

## 🆘 **仍然有問題？**

### **檢查日志**
```bash
# 查看最新日志
tail -n 100 ~/.canto-beats/logs/canto-beats_$(date +%Y%m%d).log

# 搜索錯誤
grep -i "error\|exception" ~/.canto-beats/logs/canto-beats_$(date +%Y%m%d).log
```

### **完整診斷**
```bash
source venv/bin/activate
python -c "
import sys
print(f'Python: {sys.version}')
print(f'Path: {sys.executable}')

try:
    import PySide6
    print('✅ PySide6')
except ImportError:
    print('❌ PySide6')

try:
    import mlx
    print('✅ MLX')
except ImportError:
    print('❌ MLX')

try:
    import mpv
    print('✅ python-mpv')
except ImportError:
    print('⚠️  python-mpv (可選)')
"
```

---

## 📞 **需要幫助？**

如果問題仍然存在，請提供：
1. 錯誤截圖
2. 日志文件內容
3. 您運行的命令

---

**記住：永遠在虛擬環境中運行應用程序！** 🎯
