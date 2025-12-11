-- Supabase Schema for License Management
-- Run this in your Supabase SQL Editor

-- Table: licenses (預先準備的序號)
CREATE TABLE licenses (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  license_key VARCHAR(50) UNIQUE NOT NULL,
  is_used BOOLEAN DEFAULT FALSE,
  used_at TIMESTAMPTZ,
  used_by_email VARCHAR(255),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: purchases (購買記錄)
CREATE TABLE purchases (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  stripe_session_id VARCHAR(255) UNIQUE NOT NULL,
  stripe_payment_intent VARCHAR(255),
  customer_email VARCHAR(255) NOT NULL,
  amount INTEGER NOT NULL,
  currency VARCHAR(10) DEFAULT 'hkd',
  license_key VARCHAR(50) REFERENCES licenses(license_key),
  status VARCHAR(50) DEFAULT 'completed',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for faster queries
CREATE INDEX idx_licenses_unused ON licenses(is_used) WHERE is_used = FALSE;
CREATE INDEX idx_purchases_email ON purchases(customer_email);

-- Enable Row Level Security (optional but recommended)
ALTER TABLE licenses ENABLE ROW LEVEL SECURITY;
ALTER TABLE purchases ENABLE ROW LEVEL SECURITY;

-- Policy: Only service role can access (for webhook)
CREATE POLICY "Service role only" ON licenses FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role only" ON purchases FOR ALL USING (auth.role() = 'service_role');

-- Sample: Insert some test license keys
-- INSERT INTO licenses (license_key) VALUES
--   ('CANTO-TEST-0001-ABCD'),
--   ('CANTO-TEST-0002-EFGH'),
--   ('CANTO-TEST-0003-IJKL');
