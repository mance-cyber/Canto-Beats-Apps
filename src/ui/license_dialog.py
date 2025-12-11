"""
License activation dialog for Canto-beats
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTextEdit, QMessageBox,
    QGroupBox, QProgressBar
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QIcon
from core.license_manager import LicenseManager, MachineFingerprint


class LicenseDialog(QDialog):
    """License activation dialog"""
    
    def __init__(self, license_manager: LicenseManager, parent=None):
        super().__init__(parent)
        self.license_manager = license_manager
        self.setup_ui()
        self.check_existing_license()
    
    def setup_ui(self):
        """Setup dialog UI"""
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setWindowTitle("Canto-beats 授權啟用")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("🎵 Canto-beats 專業版")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("請輸入您的授權序號以啟用軟體")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #888; font-size: 12pt;")
        layout.addWidget(subtitle)
        
        layout.addSpacing(20)
        
        # License key input group
        key_group = QGroupBox("授權序號")
        key_layout = QVBoxLayout(key_group)
        
        # Input field
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("CANTO-XXXX-XXXX-XXXX-XXXX")
        self.key_input.setFont(QFont("Consolas", 12))
        self.key_input.setMaxLength(29)  # CANTO-XXXX-XXXX-XXXX-XXXX
        self.key_input.textChanged.connect(self.format_license_key)
        key_layout.addWidget(self.key_input)
        
        # Validate button
        validate_btn = QPushButton("驗證序號")
        validate_btn.clicked.connect(self.validate_key)
        key_layout.addWidget(validate_btn)
        
        layout.addWidget(key_group)
        
        # Machine info group
        machine_group = QGroupBox("機器資訊")
        machine_layout = QVBoxLayout(machine_group)
        
        # Machine fingerprint display
        fingerprint = MachineFingerprint.generate()
        machine_info = QLabel(f"機器識別碼: {fingerprint[:16]}...")
        machine_info.setFont(QFont("Consolas", 9))
        machine_info.setStyleSheet("color: #666;")
        machine_layout.addWidget(machine_info)
        
        help_text = QLabel("⚠️ 序號將綁定到此機器，最多可轉移 1 次")
        help_text.setStyleSheet("color: #f39c12; font-size: 10pt;")
        help_text.setWordWrap(True)
        machine_layout.addWidget(help_text)
        
        layout.addWidget(machine_group)
        
        # Status display
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(120)
        self.status_text.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 10px;
                font-family: Consolas;
                font-size: 10pt;
            }
        """)
        layout.addWidget(self.status_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        
        # Add purchase button on the left - Highly visible with gradient
        purchase_btn = QPushButton("💳 立即購買")
        purchase_btn.clicked.connect(self.open_purchase_page)
        purchase_btn.setMinimumHeight(45)
        purchase_btn.setCursor(Qt.PointingHandCursor)
        purchase_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff6b6b, stop:0.5 #ee5a6f, stop:1 #f06292);
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 12pt;
                font-weight: bold;
                border: 2px solid #ff8787;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff5252, stop:0.5 #ff4081, stop:1 #f50057);
                border: 2px solid #ff6b6b;
                padding: 13px 25px;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e53935, stop:0.5 #d81b60, stop:1 #c2185b);
                padding: 11px 23px;
            }
        """)
        button_layout.addWidget(purchase_btn)


        
        button_layout.addStretch()
        
        self.activate_btn = QPushButton("啟用授權")
        self.activate_btn.setEnabled(False)
        self.activate_btn.clicked.connect(self.activate_license)
        self.activate_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #888;
            }
        """)
        button_layout.addWidget(self.activate_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #555;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #666;
            }
        """)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Set dialog style
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                border: 1px solid #444;
                border-radius: 8px;
            }
            QLabel {
                color: #e0e0e0;
            }
            QGroupBox {
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
            }
            QLineEdit {
                background-color: #2b2b2b;
                color: #e0e0e0;
                border: 2px solid #444;
                border-radius: 5px;
                padding: 8px;
                font-size: 12pt;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 16px;
                border-radius: 5px;
                border: none;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #5dade2;
            }
        """)
    
    def format_license_key(self, text: str):
        """Auto-format license key with dashes"""
        # Remove existing dashes
        text = text.replace('-', '').upper()
        
        # Add CANTO- prefix if not present
        if not text.startswith('CANTO'):
            if len(text) > 0 and not 'CANTO'.startswith(text):
                text = 'CANTO' + text
            else:
                text = 'CANTO'
        
        # Format with dashes
        formatted = 'CANTO'
        remaining = text[5:]  # After 'CANTO'
        
        for i in range(0, len(remaining), 4):
            chunk = remaining[i:i+4]
            if chunk:
                formatted += '-' + chunk
        
        # Update input if different
        if formatted != self.key_input.text():
            cursor_pos = self.key_input.cursorPosition()
            self.key_input.setText(formatted)
            self.key_input.setCursorPosition(min(cursor_pos, len(formatted)))
    
    def check_existing_license(self):
        """Check if there's an existing license"""
        is_valid, message = self.license_manager.validator.verify()
        if is_valid:
            license_info = self.license_manager.get_license_info()
            if license_info:
                self.log_status(f"✅ 已找到有效授權")
                self.log_status(f"授權類型: {license_info.license_type}")
                self.log_status(f"剩餘轉移次數: {license_info.transfers_remaining}")
                
                # Show option to continue without re-activating
                QMessageBox.information(
                    self,
                    "已授權",
                    "您的軟體已經啟用，可以直接使用！\n\n"
                    "如果您想更換序號，請輸入新的序號。",
                    QMessageBox.Ok
                )
                
                # Auto-accept dialog
                QTimer.singleShot(100, self.accept)
    
    def log_status(self, message: str):
        """Add message to status log"""
        self.status_text.append(message)
        # Auto-scroll to bottom
        scrollbar = self.status_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def validate_key(self):
        """Validate license key format"""
        key = self.key_input.text().strip()
        
        if not key:
            self.log_status("❌ 請輸入序號")
            return
        
        self.log_status(f"🔍 驗證序號: {key}")
        
        is_valid, message = self.license_manager.validate_key(key)
        
        if is_valid:
            self.log_status(f"✅ {message}")
            self.activate_btn.setEnabled(True)
        else:
            self.log_status(f"❌ {message}")
            self.activate_btn.setEnabled(False)
    
    def activate_license(self):
        """Activate the license"""
        key = self.key_input.text().strip()
        
        if not key:
            QMessageBox.warning(self, "錯誤", "請輸入序號")
            return
        
        self.log_status(f"🚀 啟用序號...")
        
        # Try activation
        success, message = self.license_manager.activate_license(key, force_transfer=False)
        
        if success:
            self.log_status(f"✅ {message}")
            QMessageBox.information(
                self,
                "成功",
                "授權啟用成功！\n\nCanto-beats 現已就緒。",
                QMessageBox.Ok
            )
            self.accept()
        else:
            # Check if it's a transfer issue
            if "已在其他機器啟用" in message:
                # Ask user if they want to transfer
                reply = QMessageBox.question(
                    self,
                    "確認轉移",
                    f"{message}\n\n是否要將授權轉移到這台機器？\n"
                    "⚠️ 此操作將減少一次轉移機會！",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # Force transfer
                    success, message = self.license_manager.activate_license(key, force_transfer=True)
                    if success:
                        self.log_status(f"✅ {message}")
                        QMessageBox.information(self, "成功", "授權已轉移到本機！")
                        self.accept()
                    else:
                        self.log_status(f"❌ {message}")
                        QMessageBox.critical(self, "錯誤", message)
            else:
                self.log_status(f"❌ {message}")
                QMessageBox.critical(self, "錯誤", message)

    def open_purchase_page(self):
        """Open purchase page in browser."""
        import webbrowser
        url = "https://yourwebsite.com/purchase"  # TODO: Replace with actual purchase page URL
        
        try:
            webbrowser.open(url)
            self.log_status(f"🌐 已開啟購買頁面: {url}")
        except Exception as e:
            self.log_status(f"❌ 無法開啟網頁: {e}")
            QMessageBox.warning(self, "錯誤", f"無法開啟網頁瀏覽器\n{str(e)}")
