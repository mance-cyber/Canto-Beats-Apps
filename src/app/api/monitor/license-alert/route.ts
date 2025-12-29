import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';
import { sendLicenseEmail } from '@/lib/email';

const LOW_LICENSE_THRESHOLD = 100;
const ADMIN_EMAIL = process.env.GMAIL_USER || 'info@cantobeats.com';

export async function POST(request: NextRequest) {
  try {
    const supabaseUrl = process.env.SUPABASE_URL;
    const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

    if (!supabaseUrl || !supabaseServiceKey) {
      return NextResponse.json({ error: 'Server configuration error' }, { status: 500 });
    }

    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    // Count available licenses
    const { count, error } = await supabase
      .from('licenses')
      .select('*', { count: 'exact', head: true })
      .eq('is_used', false);

    if (error) {
      console.error('Error checking license count:', error);
      return NextResponse.json({ error: 'Database error' }, { status: 500 });
    }

    const availableLicenses = count || 0;

    // If licenses are low, send alert email
    if (availableLicenses < LOW_LICENSE_THRESHOLD) {
      console.warn(`⚠️ LOW LICENSE ALERT: Only ${availableLicenses} licenses remaining!`);

      // Send alert email to admin
      const nodemailer = require('nodemailer');
      const transporter = nodemailer.createTransport({
        service: 'gmail',
        auth: {
          user: process.env.GMAIL_USER,
          pass: process.env.GMAIL_APP_PASSWORD,
        },
      });

      const alertHtml = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; }
    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
    .alert { background: #fee; border-left: 4px solid #f00; padding: 20px; margin: 20px 0; }
    .stats { background: #f5f5f5; padding: 15px; border-radius: 8px; }
    .stat-item { margin: 10px 0; font-size: 18px; }
    .warning { color: #d00; font-weight: bold; }
  </style>
</head>
<body>
  <div class="container">
    <h2>🚨 Canto-Beats 授權序號庫存警報</h2>

    <div class="alert">
      <p class="warning">警告：授權序號庫存不足！</p>
      <p>目前可用授權序號數量已低於警戒線。</p>
    </div>

    <div class="stats">
      <h3>當前庫存狀態</h3>
      <div class="stat-item">📦 可用序號: <strong>${availableLicenses}</strong></div>
      <div class="stat-item">⚠️ 警戒線: <strong>${LOW_LICENSE_THRESHOLD}</strong></div>
      <div class="stat-item">📊 庫存狀態: <strong class="warning">不足</strong></div>
    </div>

    <h3>建議行動</h3>
    <ol>
      <li>立即準備新的授權序號批次</li>
      <li>使用 generate-licenses.js 生成新序號</li>
      <li>導入到 Supabase 數據庫</li>
      <li>確認庫存恢復正常</li>
    </ol>

    <p style="margin-top: 30px; color: #666; font-size: 14px;">
      此警報由 Canto-Beats 監控系統自動發送<br>
      時間: ${new Date().toLocaleString('zh-HK', { timeZone: 'Asia/Hong_Kong' })}
    </p>
  </div>
</body>
</html>
      `;

      try {
        await transporter.sendMail({
          from: `"Canto-Beats Alert" <${ADMIN_EMAIL}>`,
          to: ADMIN_EMAIL,
          subject: `🚨 警報：授權序號庫存不足 (剩餘 ${availableLicenses} 個)`,
          html: alertHtml,
        });

        console.log(`Alert email sent to ${ADMIN_EMAIL}`);
      } catch (emailError) {
        console.error('Failed to send alert email:', emailError);
        // Don't fail the request if email fails
      }

      return NextResponse.json({
        alert: true,
        availableLicenses,
        threshold: LOW_LICENSE_THRESHOLD,
        message: `Low license inventory: ${availableLicenses} remaining`,
      });
    }

    return NextResponse.json({
      alert: false,
      availableLicenses,
      threshold: LOW_LICENSE_THRESHOLD,
      message: 'License inventory healthy',
    });
  } catch (error) {
    console.error('Error in license alert check:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
