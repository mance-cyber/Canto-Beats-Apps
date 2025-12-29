const nodemailer = require('nodemailer');
require('dotenv').config({ path: '.env.local' });

const transporter = nodemailer.createTransport({
  service: 'gmail',
  auth: {
    user: process.env.GMAIL_USER,
    pass: process.env.GMAIL_APP_PASSWORD,
  },
});

async function testEmail() {
  console.log('📧 Testing Gmail configuration...');
  console.log('User:', process.env.GMAIL_USER);
  console.log('Password:', process.env.GMAIL_APP_PASSWORD ? '***' + process.env.GMAIL_APP_PASSWORD.slice(-4) : 'NOT SET');

  try {
    const info = await transporter.sendMail({
      from: `"Canto-Beats Test" <${process.env.GMAIL_USER}>`,
      to: 'manceli@m-pro.com.hk',
      subject: '🧪 Canto-Beats 測試郵件',
      text: '這是一封測試郵件，用來確認 Gmail 發送功能是否正常。\n\n你的序號：CANTO-TEST-0003-IJKL',
      html: '<h1>測試成功！</h1><p>你的序號：<strong>CANTO-TEST-0003-IJKL</strong></p>',
    });

    console.log('✅ Email sent successfully!');
    console.log('Message ID:', info.messageId);
    console.log('Response:', info.response);
  } catch (error) {
    console.error('❌ Email sending failed:');
    console.error('Error code:', error.code);
    console.error('Error message:', error.message);
    if (error.response) {
      console.error('Server response:', error.response);
    }
  }
}

testEmail();
