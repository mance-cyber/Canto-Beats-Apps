# 擴展粵語校正字庫
## 目標
將校正字庫擴展到 5000+(不用一次過加,每次每項拆分50去增加) 條目，包含：
- 成語 (idioms)
- 俗語 (proverbs) 
- 潮語 (trendy phrases)
## 方案
### 1. 創建外部 JSON 檔案
- `src/resources/cantonese_corrections.json`
- 結構：`{"錯誤": "正確"}`
- 容易維護同擴展
### 2. 資料來源
- 粵語成語字典
- 香港俚語大全
- 網絡潮語集合
- Whisper 常見錯誤
### 3. 代碼修改
- 修改 [subtitle_pipeline_v2.py](file:///c:/Users/ktphi/.gemini/antigravity/playground/canto-beats/src/pipeline/subtitle_pipeline_v2.py) 從 JSON 載入
- 支援動態更新字庫
## 初步估計
| 類別 | 目標數量 |
|------|----------|
| 成語同音字 | 2000 |
| 俗語/諺語 | 1500 |
| 潮語/網絡用語 | 1000 |
| 簡繁對照 | 500 |