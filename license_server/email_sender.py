"""
Email sending functionality using SendGrid
"""

import os
import sys
from pathlib import Path
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from config import settings
from datetime import datetime

# Add parent directory to path to import license generator
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir / "src"))

from core.license_manager import LicenseGenerator


class EmailSender:
    """Email sender using SendGrid"""
    
    def __init__(self):
        self.client = SendGridAPIClient(settings.sendgrid_api_key)
        self.from_email = Email(settings.sendgrid_from_email, settings.sendgrid_from_name)
    
    def send_license_email(self, recipient_email: str, recipient_name: str, license_key: str) -> bool:
        """
        Send license key to customer
        
        Args:
            recipient_email: Customer email
            recipient_name: Customer name
            license_key: License key
            
        Returns:
            Success status
        """
        try:
            # Create email content
            subject = "您的 Canto-beats 授權序號"
            
            # HTML content
            html_content = self._create_html_email(recipient_name, license_key)
            
            # Plain text content
            text_content = self._create_text_email(recipient_name, license_key)
            
            # Create message
            message = Mail(
                from_email=self.from_email,
                to_emails=To(recipient_email, recipient_name),
                subject=subject,
                plain_text_content=Content("text/plain", text_content),
                html_content=Content("text/html", html_content)
            )
            
            # Send email
            response = self.client.send(message)
            
            if response.status_code == 202:
                print(f"✅ Email sent to {recipient_email}")
                return True
            else:
                print(f"❌ Failed to send email: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            return False
    
    def _create_html_email(self, name: str, license_key: str) -> str:
        """Create HTML email content"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang TC', 'Microsoft YaHei', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px 10px 0 0;
            text-align: center;
        }}
        .content {{
            background: #f8f9fa;
            padding: 30px;
            border-radius: 0 0 10px 10px;
        }}
        .license-box {{
            background: white;
            border: 2px solid #667eea;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
        }}
        .license-key {{
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
            letter-spacing: 2px;
            font-family: 'Courier New', monospace;
            word-break: break-all;
        }}
        .steps {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .step {{
            margin: 15px 0;
            padding-left: 30px;
            position: relative;
        }}
        .step::before {{
            content: "✓";
            position: absolute;
            left: 0;
            color: #667eea;
            font-weight: bold;
            font-size: 18px;
        }}
        .warning {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .footer {{
            text-align: center;
            color: #666;
            font-size: 14px;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎵 歡迎使用 Canto-beats！</h1>
        <p>感謝您的購買</p>
    </div>
    
    <div class="content">
        <p>親愛的 {name or '客戶'}，</p>
        
        <p>感謝您購買 <strong>Canto-beats 專業版</strong>！您的授權序號已經準備好了。</p>
        
        <div class="license-box">
            <p style="margin: 0 0 10px 0; color: #666;">您的授權序號</p>
            <div class="license-key">{license_key}</div>
        </div>
        
        <div class="steps">
            <h3 style="margin-top: 0;">📝 啟用步驟：</h3>
            <div class="step">下載並安裝 Canto-beats</div>
            <div class="step">首次啟動時會顯示授權對話框</div>
            <div class="step">輸入上述授權序號</div>
            <div class="step">點擊「啟用授權」完成綁定</div>
        </div>
        
        <div class="warning">
            <strong>⚠️ 重要提醒：</strong>
            <ul style="margin: 10px 0;">
                <li>請妥善保管您的序號</li>
                <li>序號將綁定到您的電腦</li>
                <li>您有 <strong>1 次</strong>機會轉移到其他電腦</li>
                <li>請勿將序號分享給他人</li>
            </ul>
        </div>
        
        <p>如有任何問題，請隨時聯絡我們的客戶支援團隊。</p>
        
        <p>祝您使用愉快！</p>
        <p><strong>Canto-beats 團隊</strong></p>
    </div>
    
    <div class="footer">
        <p>© {datetime.now().year} Canto-beats. All rights reserved.</p>
        <p style="font-size: 12px; color: #999;">此郵件為系統自動發送，請勿直接回覆。</p>
    </div>
</body>
</html>
        """
    
    def _create_text_email(self, name: str, license_key: str) -> str:
        """Create plain text email content"""
        return f"""
🎵 歡迎使用 Canto-beats！

親愛的 {name or '客戶'}，

感謝您購買 Canto-beats 專業版！

您的授權序號：
{license_key}

啟用步驟：
1. 下載並安裝 Canto-beats
2. 首次啟動時輸入上述序號
3. 序號將綁定到您的電腦
4. 您有 1 次機會轉移到其他電腦

重要提醒：
- 請妥善保管您的序號
- 請勿將序號分享給他人

如有任何問題，請聯絡我們的客戶支援。

祝使用愉快！
Canto-beats 團隊

─────────────────────────────
© {datetime.now().year} Canto-beats. All rights reserved.
此郵件為系統自動發送，請勿直接回覆。
        """
