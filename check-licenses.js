const { createClient } = require('@supabase/supabase-js');
require('dotenv').config({ path: '.env.local' });

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY
);

async function checkLicenses() {
  console.log('📊 檢查 Supabase 序號狀態...\n');

  // Count total licenses
  const { count: totalCount, error: totalError } = await supabase
    .from('licenses')
    .select('*', { count: 'exact', head: true });

  if (totalError) {
    console.error('❌ 錯誤:', totalError.message);
    return;
  }

  // Count unused licenses
  const { count: unusedCount, error: unusedError } = await supabase
    .from('licenses')
    .select('*', { count: 'exact', head: true })
    .eq('is_used', false);

  // Count used licenses
  const { count: usedCount, error: usedError } = await supabase
    .from('licenses')
    .select('*', { count: 'exact', head: true })
    .eq('is_used', true);

  console.log('📦 總序號數量:', totalCount);
  console.log('✅ 已使用:', usedCount);
  console.log('⚪ 可用:', unusedCount);
  console.log('');

  // Show first 5 unused licenses
  const { data: samples, error: sampleError } = await supabase
    .from('licenses')
    .select('license_key, created_at')
    .eq('is_used', false)
    .order('created_at', { ascending: false })
    .limit(5);

  if (!sampleError && samples && samples.length > 0) {
    console.log('🎫 最新的 5 個可用序號：');
    samples.forEach(l => {
      const date = new Date(l.created_at).toLocaleString('zh-HK');
      console.log(`  - ${l.license_key} (${date})`);
    });
  }

  console.log('\n' + '='.repeat(50));
  console.log(unusedCount >= 1000 ? '✅ 1000 個序號已成功加入！' : `⚠️  目前只有 ${unusedCount} 個可用序號`);
}

checkLicenses();
