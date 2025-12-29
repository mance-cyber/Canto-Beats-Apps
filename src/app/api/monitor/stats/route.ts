import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

// Low license threshold
const LOW_LICENSE_THRESHOLD = 100;

export async function GET(request: NextRequest) {
  try {
    const supabaseUrl = process.env.SUPABASE_URL;
    const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

    if (!supabaseUrl || !supabaseServiceKey) {
      return NextResponse.json({ error: 'Server configuration error' }, { status: 500 });
    }

    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    // Get license statistics
    const { data: licenses, error: licenseError } = await supabase
      .from('licenses')
      .select('is_used');

    if (licenseError) {
      console.error('Error fetching licenses:', licenseError);
      return NextResponse.json({ error: 'Failed to fetch license data' }, { status: 500 });
    }

    const totalLicenses = licenses?.length || 0;
    const usedLicenses = licenses?.filter(l => l.is_used).length || 0;
    const availableLicenses = totalLicenses - usedLicenses;

    // Get purchase statistics
    const now = new Date();
    const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

    const { data: purchases, error: purchaseError } = await supabase
      .from('purchases')
      .select('created_at');

    if (purchaseError) {
      console.error('Error fetching purchases:', purchaseError);
      return NextResponse.json({ error: 'Failed to fetch purchase data' }, { status: 500 });
    }

    const totalPurchases = purchases?.length || 0;
    const purchasesLast24h = purchases?.filter(p => new Date(p.created_at) > yesterday).length || 0;
    const purchasesLast7days = purchases?.filter(p => new Date(p.created_at) > weekAgo).length || 0;

    // Calculate usage rate
    const usageRate = totalLicenses > 0 ? ((usedLicenses / totalLicenses) * 100).toFixed(1) : '0.0';

    // Check if alert should be triggered
    const lowLicenses = availableLicenses < LOW_LICENSE_THRESHOLD;

    const stats = {
      licenses: {
        total: totalLicenses,
        available: availableLicenses,
        used: usedLicenses,
        usageRate: `${usageRate}%`,
      },
      purchases: {
        total: totalPurchases,
        last24h: purchasesLast24h,
        last7days: purchasesLast7days,
      },
      alert: {
        lowLicenses,
        threshold: LOW_LICENSE_THRESHOLD,
        message: lowLicenses
          ? `WARNING: Only ${availableLicenses} licenses remaining!`
          : 'License inventory healthy',
      },
      timestamp: new Date().toISOString(),
    };

    return NextResponse.json(stats);
  } catch (error) {
    console.error('Unexpected error in stats API:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
