import { NextRequest, NextResponse } from 'next/server';
import Stripe from 'stripe';
import { getUnusedLicense, markLicenseUsed, createPurchase, isSessionProcessed } from '@/lib/supabase';
import { sendLicenseEmail } from '@/lib/email';

export async function POST(request: NextRequest) {
  // Initialize Stripe client at runtime
  const stripeSecretKey = process.env.STRIPE_SECRET_KEY;
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;

  if (!stripeSecretKey || !webhookSecret) {
    console.error('Stripe environment variables not configured');
    return NextResponse.json({ error: 'Server configuration error' }, { status: 500 });
  }

  const stripe = new Stripe(stripeSecretKey, {
    apiVersion: '2024-11-20.acacia',
  });

  const body = await request.text();
  const signature = request.headers.get('stripe-signature');

  if (!signature) {
    return NextResponse.json({ error: 'Missing signature' }, { status: 400 });
  }

  let event: Stripe.Event;

  try {
    event = stripe.webhooks.constructEvent(body, signature, webhookSecret);
  } catch (err) {
    console.error('Webhook signature verification failed:', err);
    return NextResponse.json({ error: 'Invalid signature' }, { status: 400 });
  }

  // Handle checkout.session.completed event
  if (event.type === 'checkout.session.completed') {
    const session = event.data.object as Stripe.Checkout.Session;

    console.log('Processing checkout session:', session.id);

    // Check if already processed (prevent duplicate)
    const alreadyProcessed = await isSessionProcessed(session.id);
    if (alreadyProcessed) {
      console.log('Session already processed:', session.id);
      return NextResponse.json({ received: true, message: 'Already processed' });
    }

    const customerEmail = session.customer_details?.email;
    const customerName = session.customer_details?.name;

    if (!customerEmail) {
      console.error('No customer email found in session');
      return NextResponse.json({ error: 'No customer email' }, { status: 400 });
    }

    // Get an unused license
    const license = await getUnusedLicense();

    if (!license) {
      console.error('No available licenses!');
      // TODO: Send alert to admin
      return NextResponse.json({ error: 'No available licenses' }, { status: 500 });
    }

    // Mark license as used
    const marked = await markLicenseUsed(license.license_key, customerEmail);
    if (!marked) {
      console.error('Failed to mark license as used');
      return NextResponse.json({ error: 'Failed to assign license' }, { status: 500 });
    }

    // Create purchase record
    await createPurchase({
      stripe_session_id: session.id,
      stripe_payment_intent: session.payment_intent as string || null,
      customer_email: customerEmail,
      amount: session.amount_total || 0,
      currency: session.currency || 'hkd',
      license_key: license.license_key,
      status: 'completed',
    });

    // Send license email
    const emailSent = await sendLicenseEmail({
      to: customerEmail,
      licenseKey: license.license_key,
      customerName: customerName || undefined,
    });

    if (!emailSent) {
      console.error('Failed to send license email to:', customerEmail);
      // Purchase is recorded, admin can manually send email
    }

    // Only log full details in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`License ${license.license_key} assigned to ${customerEmail}`);
    } else {
      console.log(`License assigned to ${customerEmail}`);
    }
  }

  return NextResponse.json({ received: true });
}

// Stripe webhook needs raw body, disable body parsing
export const config = {
  api: {
    bodyParser: false,
  },
};
