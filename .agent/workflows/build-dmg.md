# Canto-beats DMG 打包流程

> ⚠️ **重要**：此流程確保每次打包都包含最新代碼修改，同時保護 MLX Whisper 功能不受影響。

## 前置檢查

打包前請確認：
- [ ] 所有代碼修改已保存
- [ ] 在開發環境測試過新功能
- [ ] MLX Whisper 語音識別功能正常

## 打包步驟

### 1. 清理舊版本並打包

```bash
cd /Users/nicleung/Public/Canto-Beats-Apps
rm -rf build dist *.spec
./build_macos_app.sh
```

// turbo

### 2. 確認 DMG 創建

當系統詢問 `是否创建 DMG 安装包? (y/N):` 時，輸入 `y` 並按 Enter。

### 3. 驗證 MLX Whisper 完整性

打包完成後，檢查 MLX 模組是否正確打包：

```bash
ls dist/Canto-beats.app/Contents/Resources/mlx/
```

應該看到以下文件/目錄：
- `mlx/core/`
- `mlx/_reprlib_fix.py`
- `mlx_whisper/`

### 4. 測試打包版本

```bash
open dist/Canto-beats.app
```

**必測項目：**
1. ✅ 應用能正常啟動
2. ✅ 授權驗證不卡住
3. ✅ 語音識別功能正常（選擇視頻 → 開始轉錄）
4. ✅ 書面語轉換功能正常

## 輸出文件位置

| 文件類型 | 路徑 |
|---------|------|
| App Bundle | `dist/Canto-beats.app` |
| DMG 安裝包 | `dist/Canto-beats.dmg` |

## 常見問題

### Q: MLX Whisper 不工作？
確認 `post_build.sh` 執行成功，它負責複製 MLX 模組到 app bundle。

### Q: 打包失敗？
1. 確保虛擬環境已啟動：`source venv/bin/activate`
2. 確保所有依賴已安裝：`pip install -r requirements.txt`

### Q: 應用啟動後閃退？
查看日誌：`cat ~/.canto-beats/logs/canto-beats_*.log.enc`
