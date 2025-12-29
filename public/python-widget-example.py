"""
Canto-Beats 動畫 Widget - PyQt6 範例
=====================================

安裝依賴：
    pip install PyQt6 PyQt6-WebEngine

使用方法：
    python python-widget-example.py

或者嵌入到你嘅應用程式：
    from animation_widget import AnimationWidget
    widget = AnimationWidget()
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QColor


class AnimationWidget(QWebEngineView):
    """可重用嘅動畫 Widget"""

    def __init__(self, parent=None, html_path=None):
        super().__init__(parent)

        # 設定透明背景
        self.page().setBackgroundColor(QColor(15, 23, 42))  # #0f172a

        # 載入 HTML
        if html_path and os.path.exists(html_path):
            self.load(QUrl.fromLocalFile(html_path))
        else:
            # 使用內嵌 HTML
            self.setHtml(self._get_embedded_html())

    def _get_embedded_html(self):
        """內嵌 HTML（如果冇外部檔案）"""
        return '''
<!DOCTYPE html>
<html lang="zh-HK">
<head>
  <meta charset="UTF-8">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      background: #0f172a;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    .animation-container {
      position: relative;
      width: 100%;
      max-width: 500px;
      height: 200px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
    }
    .track-container {
      position: relative;
      width: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      height: 120px;
    }
    .track {
      position: absolute;
      width: 75%;
      height: 8px;
      background: #1e293b;
      border-radius: 9999px;
      overflow: hidden;
    }
    .track-glow {
      width: 100%;
      height: 100%;
      background: linear-gradient(90deg, transparent, #ff5400, transparent);
      animation: flowLine 2s linear infinite;
      opacity: 0.3;
    }
    .video-icon {
      position: absolute;
      z-index: 10;
      animation: videoSlide 4s ease-in-out infinite;
    }
    .icon-box {
      width: 64px;
      height: 64px;
      border-radius: 12px;
      border: 2px solid;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
    }
    .video-box {
      background: #334155;
      border-color: #64748b;
      color: #cbd5e1;
      box-shadow: 0 10px 25px rgba(0,0,0,0.3);
    }
    .srt-box {
      background: white;
      border-color: #ff5400;
      color: #ff5400;
      box-shadow: 0 0 20px rgba(255, 84, 0, 0.4);
    }
    .icon-box svg { width: 32px; height: 32px; }
    .badge {
      position: absolute;
      top: -8px;
      right: -8px;
      background: #3b82f6;
      color: white;
      font-size: 10px;
      font-weight: bold;
      padding: 2px 6px;
      border-radius: 9999px;
    }
    .badge.srt { background: #ff5400; }
    .app-interface {
      position: relative;
      z-index: 20;
      width: 176px;
      height: 128px;
      background: #0f172a;
      border-radius: 12px;
      border: 2px solid #475569;
      display: flex;
      flex-direction: column;
      box-shadow: 0 25px 50px rgba(0,0,0,0.5);
      overflow: hidden;
      animation: chipPulse 4s ease-in-out infinite;
    }
    .app-titlebar {
      height: 24px;
      background: #1e293b;
      border-bottom: 1px solid #334155;
      display: flex;
      align-items: center;
      padding: 0 12px;
      gap: 6px;
    }
    .dot { width: 10px; height: 10px; border-radius: 50%; }
    .dot.red { background: #ef4444; }
    .dot.yellow { background: #eab308; }
    .dot.green { background: #22c55e; }
    .app-content {
      flex: 1;
      position: relative;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
    }
    .idle-state, .processing-state {
      position: absolute;
      inset: 0;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 8px;
    }
    .idle-state { animation: idleAnim 4s ease-in-out infinite; }
    .processing-state { animation: processingAnim 4s ease-in-out infinite; gap: 12px; }
    .idle-bar { height: 6px; background: #334155; border-radius: 9999px; }
    .idle-bar:nth-child(1) { width: 75%; }
    .idle-bar:nth-child(2) { width: 50%; }
    .idle-bar:nth-child(3) { width: 66%; }
    .wave-bars { display: flex; align-items: center; gap: 4px; height: 32px; }
    .wave-bar {
      width: 4px;
      background: #ff5400;
      border-radius: 9999px;
      animation: waveBar 0.6s ease-in-out infinite;
    }
    .wave-bar:nth-child(1) { animation-delay: 0s; }
    .wave-bar:nth-child(2) { animation-delay: 0.1s; }
    .wave-bar:nth-child(3) { animation-delay: 0.2s; }
    .wave-bar:nth-child(4) { animation-delay: 0.3s; }
    .wave-bar:nth-child(5) { animation-delay: 0.4s; }
    .srt-icon {
      position: absolute;
      z-index: 10;
      animation: srtSlide 4s ease-in-out infinite;
    }
    .status-text {
      margin-top: 24px;
      font-size: 14px;
      font-family: monospace;
      font-weight: bold;
      letter-spacing: 1px;
    }
    @keyframes flowLine { 0% { transform: translateX(-100%); } 100% { transform: translateX(100%); } }
    @keyframes videoSlide {
      0%, 10% { transform: translateX(-140px); opacity: 1; }
      25%, 35% { transform: translateX(-60px); opacity: 1; }
      45%, 55% { transform: translateX(-60px); opacity: 0; }
      100% { transform: translateX(-140px); opacity: 0; }
    }
    @keyframes srtSlide {
      0%, 45% { transform: translateX(60px); opacity: 0; }
      55%, 65% { transform: translateX(60px); opacity: 1; }
      75%, 85% { transform: translateX(140px); opacity: 1; }
      100% { transform: translateX(60px); opacity: 0; }
    }
    @keyframes chipPulse {
      0%, 25% { box-shadow: 0 25px 50px rgba(0,0,0,0.5); }
      35%, 65% { box-shadow: 0 25px 50px rgba(0,0,0,0.5), 0 0 30px rgba(255,84,0,0.3); }
      75%, 100% { box-shadow: 0 25px 50px rgba(0,0,0,0.5); }
    }
    @keyframes idleAnim { 0%, 25% { opacity: 1; } 35%, 65% { opacity: 0; } 75%, 100% { opacity: 1; } }
    @keyframes processingAnim { 0%, 25% { opacity: 0; } 35%, 65% { opacity: 1; } 75%, 100% { opacity: 0; } }
    @keyframes waveBar { 0%, 100% { height: 8px; } 50% { height: 24px; } }
  </style>
</head>
<body>
  <div class="animation-container">
    <div class="track-container">
      <div class="track"><div class="track-glow"></div></div>
      <div class="video-icon">
        <div class="icon-box video-box">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          <span class="badge">MP4</span>
        </div>
      </div>
      <div class="app-interface">
        <div class="app-titlebar">
          <div class="dot red"></div>
          <div class="dot yellow"></div>
          <div class="dot green"></div>
        </div>
        <div class="app-content">
          <div class="idle-state">
            <div class="idle-bar"></div>
            <div class="idle-bar"></div>
            <div class="idle-bar"></div>
          </div>
          <div class="processing-state">
            <div class="wave-bars">
              <div class="wave-bar"></div>
              <div class="wave-bar"></div>
              <div class="wave-bar"></div>
              <div class="wave-bar"></div>
              <div class="wave-bar"></div>
            </div>
          </div>
        </div>
      </div>
      <div class="srt-icon">
        <div class="icon-box srt-box">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span class="badge srt">SRT</span>
        </div>
      </div>
    </div>
    <div class="status-text" id="statusText" style="color: #94a3b8;">1. 拖入影片檔案...</div>
  </div>
  <script>
    const texts = [
      { text: "1. 拖入影片檔案...", color: "#94a3b8" },
      { text: "2. 生成器 AI 運算中...", color: "#ff5400" },
      { text: "3. 成功匯出 SRT 字幕！", color: "#4ade80" }
    ];
    let i = 0;
    setInterval(() => { i = (i + 1) % 3; const el = document.getElementById('statusText'); el.textContent = texts[i].text; el.style.color = texts[i].color; }, 1333);
  </script>
</body>
</html>
        '''


class MainWindow(QMainWindow):
    """範例主視窗"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Canto-Beats Animation Widget Demo")
        self.setMinimumSize(600, 400)

        # 設定深色背景
        self.setStyleSheet("background-color: #0f172a;")

        # 主 layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)

        # 動畫 widget
        self.animation = AnimationWidget()
        self.animation.setMinimumHeight(250)
        layout.addWidget(self.animation)

        # 按鈕區域
        button_layout = QHBoxLayout()

        start_btn = QPushButton("開始處理")
        start_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff5400;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e64a00;
            }
        """)

        button_layout.addStretch()
        button_layout.addWidget(start_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)


def main():
    app = QApplication(sys.argv)

    # 設定應用程式樣式
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
