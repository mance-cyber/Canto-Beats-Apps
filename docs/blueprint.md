# **App Name**: 字能聽

## Core Features:

- 即時網頁Demo: 畀用家喺網頁即時上傳或者錄製60秒嘅Cantonese音頻/影片，然後顯示real-time Cantonese轉錄文字（但係網頁版冇SRT下載）。Use a mock API to return Cantonese transcript
- 音頻/影片上傳: 畀用家喺網頁demo上傳本地音頻或者影片檔案嚟做轉錄測試。
- 即時錄音: 畀用家喺網頁demo直接錄製音頻嚟做轉錄測試。
- 下載Windows版本: 提供連結以下載最新Windows版本嘅App
- 下載MacOS版本: 提供連結以下載最新macOS版本嘅App
- 下載Linux版本: 提供連結以下載最新Linux AppImage版本嘅App
- 生成獨特License Key: 成功付款後，Firebase Cloud Function會生成一個獨特嘅16字元License Key（格式：XXXX-XXXX-XXXX-XXXX），儲存喺Firestore collection “licenses”，然後喺頁面顯示並透過email發送（用Firebase Extensions “Trigger Email”）。

## Style Guidelines:

- 基於親切、可靠的感覺，選擇淺色系。
- Primary color: 柔和的藍色 (#A0C4FF)，給人一種科技感同專業感。呢隻顏色喺淺色背景上面夠突出，但又唔會太刺眼。
- Background color: 極淡嘅藍色 (#F0F8FF)，提供一個乾淨、整潔嘅背景。
- Accent color: 明亮嘅橙色 (#FFA500)，用於CTA按鈕同埋重要嘅highlight，增加視覺焦點。
- Body and headline font: 用'PT Sans'，呢隻字體modern又帶點人情味，啱晒用喺標題同內文。
- 用lucide-react icons，簡潔又modern。
- 100% mobile responsive，喺唔同尺寸嘅螢幕上面都呈現最佳效果。
- 加入一啲Subtle animations，例如smooth scroll效果，提升用戶體驗。
- Note: currently only Google Fonts are supported.