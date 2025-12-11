const { createClient } = require('@supabase/supabase-js');
require('dotenv').config({ path: '.env.local' });

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY
);

async function checkStatus() {
  // Check latest purchases
  const { data: purchases, error: purchaseError } = await supabase
    .from('purchases')
    .select('*')
    .order('created_at', { ascending: false })
    .limit(3);

  console.log('\n📦 Latest Purchases:');
  if (purchaseError) {
    console.error('Error:', purchaseError.message);
  } else {
    purchases.forEach(p => {
      console.log(`  - ${p.customer_email} | ${p.license_key} | ${p.created_at}`);
    });
  }

  // Check license status
  const { data: licenses, error: licenseError } = await supabase
    .from('licenses')
    .select('*')
    .order('used_at', { ascending: false, nullsFirst: false });

  console.log('\n🎫 License Status:');
  if (licenseError) {
    console.error('Error:', licenseError.message);
  } else {
    licenses.forEach(l => {
      const status = l.is_used ? '✅ USED' : '⚪ AVAILABLE';
      console.log(`  ${status} | ${l.license_key} | ${l.used_by_email || 'N/A'}`);
    });
  }
}

checkStatus();
