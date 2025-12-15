-- ==================== Canto-beats 軟件授權系統 ====================
-- 使用 app_licenses 表名，避免與現有 licenses 表衝突
-- 在 Supabase SQL Editor 執行

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 軟件授權表（改名為 app_licenses）
CREATE TABLE IF NOT EXISTS app_licenses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    license_key TEXT UNIQUE NOT NULL,
    license_type TEXT DEFAULT 'permanent',
    transfers_allowed INTEGER DEFAULT 1,
    transfers_used INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    email TEXT,
    notes TEXT
);

-- 機器啟用記錄表
CREATE TABLE IF NOT EXISTS app_activations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    license_id UUID NOT NULL REFERENCES app_licenses(id),
    machine_fingerprint TEXT NOT NULL,
    activated_at TIMESTAMPTZ DEFAULT NOW(),
    last_verified_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    UNIQUE(license_id, machine_fingerprint)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_app_licenses_key ON app_licenses(license_key);
CREATE INDEX IF NOT EXISTS idx_app_activations_license ON app_activations(license_id);

-- 從舊 licenses 表導入序號（可選 - 根據你的舊表結構調整）
-- 如果你的舊表有 is_used 欄位，取消下面的註釋
/*
INSERT INTO app_licenses (license_key, license_type, transfers_allowed, transfers_used, created_at, email)
SELECT 
    UPPER(license_key) as license_key,
    'permanent' as license_type,
    1 as transfers_allowed,
    CASE WHEN is_used THEN 1 ELSE 0 END as transfers_used,
    created_at,
    used_by_email as email
FROM licenses
ON CONFLICT (license_key) DO NOTHING;
*/

-- 如果只想導入 license_key，使用這個簡單版本：
INSERT INTO app_licenses (license_key, license_type, transfers_allowed)
SELECT 
    UPPER(license_key) as license_key,
    'permanent' as license_type,
    1 as transfers_allowed
FROM licenses
ON CONFLICT (license_key) DO NOTHING;

-- RPC 函數：啟用授權
CREATE OR REPLACE FUNCTION activate_license(
    p_license_key TEXT,
    p_machine_fingerprint TEXT,
    p_force_transfer BOOLEAN DEFAULT false
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_license RECORD;
    v_activation RECORD;
    v_active_count INTEGER;
BEGIN
    SELECT * INTO v_license FROM app_licenses WHERE license_key = UPPER(p_license_key);
    
    IF v_license IS NULL THEN
        RETURN jsonb_build_object('success', false, 'message', '序號不存在');
    END IF;
    
    SELECT * INTO v_activation 
    FROM app_activations 
    WHERE license_id = v_license.id 
      AND machine_fingerprint = p_machine_fingerprint 
      AND is_active = true;
    
    IF v_activation IS NOT NULL THEN
        UPDATE app_activations SET last_verified_at = NOW() WHERE id = v_activation.id;
        RETURN jsonb_build_object(
            'success', true, 
            'message', '授權有效',
            'already_activated', true
        );
    END IF;
    
    SELECT COUNT(*) INTO v_active_count 
    FROM app_activations 
    WHERE license_id = v_license.id AND is_active = true;
    
    IF v_active_count >= 1 THEN
        IF v_license.transfers_used >= v_license.transfers_allowed THEN
            RETURN jsonb_build_object(
                'success', false, 
                'message', '轉移次數已用完',
                'transfers_used', v_license.transfers_used,
                'transfers_allowed', v_license.transfers_allowed
            );
        END IF;
        
        IF NOT p_force_transfer THEN
            RETURN jsonb_build_object(
                'success', false, 
                'message', '序號已在其他機器啟用，需要轉移',
                'require_transfer', true,
                'transfers_remaining', v_license.transfers_allowed - v_license.transfers_used
            );
        END IF;
        
        UPDATE app_activations SET is_active = false 
        WHERE license_id = v_license.id AND is_active = true;
        
        UPDATE app_licenses SET transfers_used = transfers_used + 1 
        WHERE id = v_license.id;
    END IF;
    
    INSERT INTO app_activations (license_id, machine_fingerprint)
    VALUES (v_license.id, p_machine_fingerprint);
    
    RETURN jsonb_build_object('success', true, 'message', '授權成功！');
END;
$$;

-- RPC 函數：驗證授權
CREATE OR REPLACE FUNCTION verify_license(
    p_license_key TEXT,
    p_machine_fingerprint TEXT
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_license RECORD;
    v_activation RECORD;
BEGIN
    SELECT * INTO v_license FROM app_licenses WHERE license_key = UPPER(p_license_key);
    
    IF v_license IS NULL THEN
        RETURN jsonb_build_object('success', false, 'message', '序號不存在');
    END IF;
    
    SELECT * INTO v_activation 
    FROM app_activations 
    WHERE license_id = v_license.id 
      AND machine_fingerprint = p_machine_fingerprint 
      AND is_active = true;
    
    IF v_activation IS NULL THEN
        RETURN jsonb_build_object('success', false, 'message', '此機器未授權');
    END IF;
    
    UPDATE app_activations SET last_verified_at = NOW() WHERE id = v_activation.id;
    
    RETURN jsonb_build_object(
        'success', true, 
        'message', '授權有效',
        'license_type', v_license.license_type,
        'activated_at', v_activation.activated_at
    );
END;
$$;

-- 查看結果
SELECT '創建完成！' as status, COUNT(*) as total_licenses FROM app_licenses;
