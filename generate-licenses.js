// 生成 1000 個序號的 SQL
function generateLicenseKey(num) {
  const prefix = 'CANTO';
  const year = '2025';
  const serial = String(num).padStart(4, '0');
  const random = Math.random().toString(36).substring(2, 6).toUpperCase();
  return `${prefix}-${year}-${serial}-${random}`;
}

console.log('-- 批量插入 1000 個序號');
console.log('-- 複製以下 SQL 到 Supabase SQL Editor 執行\n');
console.log('INSERT INTO licenses (license_key) VALUES');

const values = [];
for (let i = 1; i <= 1000; i++) {
  values.push(`  ('${generateLicenseKey(i)}')`);
}

console.log(values.join(',\n'));
console.log('ON CONFLICT (license_key) DO NOTHING;');
console.log('\n-- 完成！這將加入 1000 個唯一序號');
