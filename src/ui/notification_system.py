"""
Notification System for Canto-beats
Handles in-app notifications, updates, and announcements
"""

import json
import os
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from PySide6.QtCore import QObject, Signal, QTimer, QThread
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QWidget, QFrame
)
from PySide6.QtCore import Qt

from utils.logger import setup_logger

logger = setup_logger()


class NotificationFetcher(QThread):
    """Background thread to fetch notifications"""
    notifications_fetched = Signal(list)
    
    def __init__(self, url: str):
        super().__init__()
        self.url = url
    
    def run(self):
        try:
            # SECURITY: Ensure SSL certificate verification is enabled
            response = requests.get(self.url, timeout=5, verify=True)
            if response.status_code == 200:
                data = response.json()
                self.notifications_fetched.emit(data.get('notifications', []))
        except Exception as e:
            logger.debug(f"Failed to fetch notifications: {e}")
            # Return empty on failure
            self.notifications_fetched.emit([])


class NotificationManager(QObject):
    """
    Manages notifications for the application.
    
    Features:
    - Fetches notifications from remote server
    - Falls back to local notifications file
    - Tracks read/unread status
    - Emits signals when new notifications arrive
    """
    
    notification_count_changed = Signal(int)
    new_notification = Signal(dict)
    
    # Remote URL for notifications (can be changed to your server)
    NOTIFICATIONS_URL = "https://raw.githubusercontent.com/user/canto-beats/main/notifications.json"
    
    def __init__(self, app_dir: str = None):
        super().__init__()
        
        # Setup paths
        if app_dir:
            self.app_dir = Path(app_dir)
        else:
            self.app_dir = Path.home() / ".canto_beats"
        
        self.app_dir.mkdir(parents=True, exist_ok=True)
        
        # Local files
        self.notifications_file = self.app_dir / "notifications.json"
        self.read_status_file = self.app_dir / "notifications_read.json"
        
        # Notifications storage
        self._notifications: List[Dict] = []
        self._read_ids: set = set()
        
        # Load read status
        self._load_read_status()
        
        # Load initial local notifications
        self._load_local_notifications()
        
        # Setup auto-refresh timer (check every 30 minutes)
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self.refresh)
        self._refresh_timer.start(30 * 60 * 1000)  # 30 minutes
        
        # Fetcher thread
        self._fetcher = None
    
    def _load_read_status(self):
        """Load which notifications have been read"""
        try:
            if self.read_status_file.exists():
                with open(self.read_status_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._read_ids = set(data.get('read_ids', []))
        except Exception as e:
            logger.debug(f"Failed to load read status: {e}")
            self._read_ids = set()
    
    def _save_read_status(self):
        """Save which notifications have been read"""
        try:
            with open(self.read_status_file, 'w', encoding='utf-8') as f:
                json.dump({'read_ids': list(self._read_ids)}, f)
        except Exception as e:
            logger.debug(f"Failed to save read status: {e}")
    
    def _load_local_notifications(self):
        """Load notifications from local file"""
        # Default notifications (bundled with app)
        default_notifications = [
            {
                "id": "welcome_v1",
                "title": "歡迎使用 Canto-beats!",
                "message": "感謝你選擇 Canto-beats 粵語字幕神器！如有任何問題，歡迎聯絡我們。",
                "date": "2024-12-05",
                "type": "info"
            },
            {
                "id": "tips_v1",
                "title": "使用小貼士",
                "message": "拖入影片後點擊「開始 AI 轉寫」即可自動生成字幕。可以在右側面板調整字幕風格。",
                "date": "2024-12-05",
                "type": "tip"
            }
        ]
        
        try:
            if self.notifications_file.exists():
                with open(self.notifications_file, 'r', encoding='utf-8') as f:
                    self._notifications = json.load(f)
            else:
                self._notifications = default_notifications
                self._save_notifications()
        except Exception as e:
            logger.debug(f"Failed to load notifications: {e}")
            self._notifications = default_notifications
    
    def _save_notifications(self):
        """Save notifications to local file"""
        try:
            with open(self.notifications_file, 'w', encoding='utf-8') as f:
                json.dump(self._notifications, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.debug(f"Failed to save notifications: {e}")
    
    def refresh(self):
        """Refresh notifications from remote server"""
        if self._fetcher and self._fetcher.isRunning():
            return
        
        self._fetcher = NotificationFetcher(self.NOTIFICATIONS_URL)
        self._fetcher.notifications_fetched.connect(self._on_notifications_fetched)
        self._fetcher.start()
    
    def _on_notifications_fetched(self, notifications: List[Dict]):
        """Handle fetched notifications"""
        if not notifications:
            return
        
        # Check for new notifications
        existing_ids = {n.get('id') for n in self._notifications}
        new_notifications = [n for n in notifications if n.get('id') not in existing_ids]
        
        if new_notifications:
            self._notifications = notifications + [
                n for n in self._notifications 
                if n.get('id') not in {nn.get('id') for nn in notifications}
            ]
            self._save_notifications()
            
            # Emit signal for each new notification
            for n in new_notifications:
                self.new_notification.emit(n)
        
        # Update count
        self.notification_count_changed.emit(self.unread_count)
    
    @property
    def notifications(self) -> List[Dict]:
        """Get all notifications, sorted by date (newest first)"""
        return sorted(
            self._notifications, 
            key=lambda x: x.get('date', ''), 
            reverse=True
        )
    
    @property
    def unread_count(self) -> int:
        """Get count of unread notifications"""
        return len([n for n in self._notifications if n.get('id') not in self._read_ids])
    
    def mark_as_read(self, notification_id: str):
        """Mark a notification as read"""
        self._read_ids.add(notification_id)
        self._save_read_status()
        self.notification_count_changed.emit(self.unread_count)
    
    def mark_all_as_read(self):
        """Mark all notifications as read"""
        for n in self._notifications:
            if n.get('id'):
                self._read_ids.add(n['id'])
        self._save_read_status()
        self.notification_count_changed.emit(self.unread_count)
    
    def is_read(self, notification_id: str) -> bool:
        """Check if a notification has been read"""
        return notification_id in self._read_ids
    
    def add_local_notification(self, title: str, message: str, notification_type: str = "info"):
        """Add a local notification (for app-generated notifications)"""
        notification = {
            "id": f"local_{datetime.now().timestamp()}",
            "title": title,
            "message": message,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "type": notification_type
        }
        self._notifications.insert(0, notification)
        self._save_notifications()
        self.new_notification.emit(notification)
        self.notification_count_changed.emit(self.unread_count)


class NotificationDialog(QDialog):
    """Dialog to display notifications"""
    
    def __init__(self, manager: NotificationManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setWindowTitle("通知中心")
        self.setMinimumWidth(500)
        self.setMinimumHeight(550)
        
        # Modern Dark Theme Styling
        self.setStyleSheet("""
            QDialog {
                background-color: #121212;
                color: #e0e0e0;
                border: 1px solid #2d2d2d;
                border-radius: 8px;
            }
            QLabel {
                color: #e0e0e0;
                border: none;
                background: transparent;
            }
            QPushButton {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #3d3d3d;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border-color: #4d4d4d;
            }
            QPushButton#primaryBtn {
                background-color: #0078d4;
                color: white;
                border: none;
            }
            QPushButton#primaryBtn:hover {
                background-color: #106ebe;
            }
            QPushButton#textBtn {
                background-color: transparent;
                border: none;
                color: #0078d4;
            }
            QPushButton#textBtn:hover {
                color: #2b88d8;
                text-decoration: underline;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #1e1e1e;
                width: 8px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #424242;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Header
        header_layout = QHBoxLayout()
        
        # Title with Icon
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        
        title = QLabel("通知中心")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        
        subtitle = QLabel("查看最新的更新與消息")
        subtitle.setStyleSheet("font-size: 13px; color: #888888;")
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header_layout.addLayout(title_layout)
        
        header_layout.addStretch()
        
        # Close button
        close_x_btn = QPushButton("✕")
        close_x_btn.setFixedSize(32, 32)
        close_x_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #888888;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #2d2d2d;
                color: #ef4444;
                border-radius: 4px;
            }
        """)
        close_x_btn.clicked.connect(self.accept)
        header_layout.addWidget(close_x_btn)
        
        # Mark all read button
        mark_all_btn = QPushButton("全部已讀")
        mark_all_btn.setObjectName("textBtn")
        mark_all_btn.setCursor(Qt.PointingHandCursor)
        mark_all_btn.clicked.connect(self._mark_all_read)
        header_layout.addWidget(mark_all_btn)
        
        layout.addLayout(header_layout)
        
        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #2d2d2d; border: none; max-height: 1px;")
        layout.addWidget(line)
        
        # Notifications list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")
        self.notifications_layout = QVBoxLayout(scroll_content)
        self.notifications_layout.setSpacing(16)
        self.notifications_layout.setContentsMargins(0, 0, 4, 0) # Right padding for scrollbar
        self.notifications_layout.setAlignment(Qt.AlignTop)
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)
        
        # Load notifications
        self._load_notifications()
        
        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        
        close_btn = QPushButton("關閉")
        close_btn.setObjectName("primaryBtn")
        close_btn.setMinimumWidth(100)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(close_btn)
        
        layout.addLayout(footer_layout)
    
    def _load_notifications(self):
        """Load and display notifications"""
        # Clear existing
        while self.notifications_layout.count():
            child = self.notifications_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        notifications = self.manager.notifications
        
        if not notifications:
            container = QWidget()
            vbox = QVBoxLayout(container)
            vbox.setSpacing(10)
            vbox.setAlignment(Qt.AlignCenter)
            
            icon_label = QLabel("--")
            icon_label.setStyleSheet("font-size: 48px;")
            icon_label.setAlignment(Qt.AlignCenter)
            
            text_label = QLabel("暫無新通知")
            text_label.setStyleSheet("color: #666666; font-size: 16px; font-weight: 500;")
            text_label.setAlignment(Qt.AlignCenter)
            
            vbox.addWidget(icon_label)
            vbox.addWidget(text_label)
            
            self.notifications_layout.addWidget(container)
        else:
            for notification in notifications:
                card = self._create_notification_card(notification)
                self.notifications_layout.addWidget(card)
    
    def _create_notification_card(self, notification: Dict) -> QFrame:
        """Create a notification card widget"""
        is_read = self.manager.is_read(notification.get('id', ''))
        
        card = QFrame()
        # Ensure no accidental borders or brackets from parent styles
        card.setObjectName("notificationCard")
        
        bg_color = "#1e1e1e" if is_read else "#252526"
        border_color = "#333333"
        hover_color = "#2a2a2a" if is_read else "#323233"
        
        # Card styling
        card.setStyleSheet(f"""
            QFrame#notificationCard {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
            }}
            QFrame#notificationCard:hover {{
                background-color: {hover_color};
                border-color: #444444;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Header row
        header = QHBoxLayout()
        header.setSpacing(10)
        
        # Unread indicator
        if not is_read:
            dot = QLabel("●")
            dot.setStyleSheet("color: #0078d4; font-size: 10px; margin-top: 2px;")
            header.addWidget(dot)
        
        # Type icon mapping
        type_icons = {
            "info": "[i]",
            "tip": "[*]",
            "update": "",
            "warning": "[!]",
            "important": "[!!]"
        }
        icon_text = type_icons.get(notification.get('type', 'info'), "[i]")
        icon = QLabel(icon_text)
        icon.setStyleSheet("font-size: 14px; background: transparent; border: none;")
        header.addWidget(icon)
        
        # Title
        title_text = notification.get('title', '通知')
        title = QLabel(title_text)
        title_color = "#ffffff" if not is_read else "#cccccc"
        title.setStyleSheet(f"""
            font-weight: 600; 
            font-size: 14px; 
            color: {title_color};
            background: transparent;
            border: none;
        """)
        header.addWidget(title, 1) # Stretch factor 1 to push date
        
        # Date
        date_text = notification.get('date', '')
        date = QLabel(date_text)
        date.setStyleSheet("""
            color: #666666; 
            font-size: 12px;
            background: transparent;
            border: none;
        """)
        header.addWidget(date)
        
        layout.addLayout(header)
        
        # Message content
        message_text = notification.get('message', '')
        message = QLabel(message_text)
        message.setWordWrap(True)
        message.setStyleSheet(f"""
            color: {'#aaaaaa' if is_read else '#dddddd'};
            font-size: 13px;
            line-height: 1.4;
            padding-left: {24 if not is_read else 14}px; /* Align with title */
            background: transparent;
            border: none;
        """)
        layout.addWidget(message)
        
        # Click handler to mark as read
        if not is_read:
            card.setCursor(Qt.PointingHandCursor)
            card.mousePressEvent = lambda e, nid=notification.get('id'): self._on_card_click(nid)
        
        return card
    
    def _on_card_click(self, notification_id: str):
        """Handle notification card click"""
        self.manager.mark_as_read(notification_id)
        self._load_notifications()
    
    def _mark_all_read(self):
        """Mark all notifications as read"""
        self.manager.mark_all_as_read()
        self._load_notifications()

