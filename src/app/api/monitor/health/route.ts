import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';
import Stripe from 'stripe';

export async function GET(request: NextRequest) {
  const health = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    services: {
      database: 'unknown',
      stripe: 'unknown',
      email: 'unknown',
    },
    environment: process.env.NODE_ENV || 'development',
  };

  // Check Supabase connection
  try {
    const supabaseUrl = process.env.SUPABASE_URL;
    const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

    if (!supabaseUrl || !supabaseServiceKey) {
      health.services.database = 'misconfigured';
    } else {
      const supabase = createClient(supabaseUrl, supabaseServiceKey);
      const { error } = await supabase.from('licenses').select('id').limit(1);

      if (error) {
        health.services.database = 'error';
        console.error('Database health check failed:', error);
      } else {
        health.services.database = 'healthy';
      }
    }
  } catch (error) {
    health.services.database = 'error';
    console.error('Database health check exception:', error);
  }

  // Check Stripe configuration
  try {
    const stripeSecretKey = process.env.STRIPE_SECRET_KEY;

    if (!stripeSecretKey) {
      health.services.stripe = 'misconfigured';
    } else {
      const stripe = new Stripe(stripeSecretKey, {
        apiVersion: '2024-11-20.acacia',
      });

      // Simple check - just verify API key format
      await stripe.balance.retrieve();
      health.services.stripe = 'healthy';
    }
  } catch (error: any) {
    if (error?.type === 'StripeAuthenticationError') {
      health.services.stripe = 'misconfigured';
    } else {
      health.services.stripe = 'error';
    }
    console.error('Stripe health check failed:', error);
  }

  // Check Email configuration
  try {
    const gmailUser = process.env.GMAIL_USER;
    const gmailPassword = process.env.GMAIL_APP_PASSWORD;

    if (!gmailUser || !gmailPassword) {
      health.services.email = 'misconfigured';
    } else if (gmailPassword.length !== 19) { // "xxxx xxxx xxxx xxxx" = 19 chars with spaces
      health.services.email = 'misconfigured';
    } else {
      health.services.email = 'configured'; // Can't test SMTP without actually sending
    }
  } catch (error) {
    health.services.email = 'error';
    console.error('Email health check failed:', error);
  }

  // Determine overall status
  const services = Object.values(health.services);
  if (services.includes('error')) {
    health.status = 'degraded';
  } else if (services.includes('misconfigured')) {
    health.status = 'unhealthy';
  } else if (services.every(s => s === 'healthy' || s === 'configured')) {
    health.status = 'healthy';
  }

  const statusCode = health.status === 'healthy' ? 200 : 503;

  return NextResponse.json(health, { status: statusCode });
}
