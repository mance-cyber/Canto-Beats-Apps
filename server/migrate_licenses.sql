-- ==================== 完整遷移腳本 ====================
-- 將舊 licenses 表遷移到新結構
-- 執行前請備份你的數據！

-- Step 1: 重命名舊表
ALTER TABLE licenses RENAME TO licenses_old;

-- Step 2: 創建新表結構（從 supabase_schema.sql 複製）
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE licenses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    license_key TEXT UNIQUE NOT NULL,
    license_type TEXT DEFAULT 'permanent',
    transfers_allowed INTEGER DEFAULT 1,
    transfers_used INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    email TEXT,
    notes TEXT
);

CREATE TABLE activations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    license_id UUID NOT NULL REFERENCES licenses(id),
    machine_fingerprint TEXT NOT NULL,
    activated_at TIMESTAMPTZ DEFAULT NOW(),
    last_verified_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    UNIQUE(license_id, machine_fingerprint)
);

CREATE INDEX IF NOT EXISTS idx_licenses_key ON licenses(license_key);
CREATE INDEX IF NOT EXISTS idx_activations_license ON activations(license_id);

-- Step 3: 從舊表導入序號到新表
INSERT INTO licenses (license_key, license_type, transfers_allowed, transfers_used, created_at, email)
SELECT 
    UPPER(license_key) as license_key,
    'permanent' as license_type,
    1 as transfers_allowed,
    CASE WHEN is_used THEN 1 ELSE 0 END as transfers_used,
    created_at,
    used_by_email as email
FROM licenses_old;

-- Step 4: 驗證遷移結果
SELECT 
    (SELECT COUNT(*) FROM licenses_old) as old_count,
    (SELECT COUNT(*) FROM licenses) as new_count;

-- Step 5: 創建 RPC 函數（從 supabase_schema.sql 複製）
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
    SELECT * INTO v_license FROM licenses WHERE license_key = UPPER(p_license_key);
    
    IF v_license IS NULL THEN
        RETURN jsonb_build_object('success', false, 'message', '序號不存在');
    END IF;
    
    SELECT * INTO v_activation 
    FROM activations 
    WHERE license_id = v_license.id 
      AND machine_fingerprint = p_machine_fingerprint 
      AND is_active = true;
    
    IF v_activation IS NOT NULL THEN
        UPDATE activations SET last_verified_at = NOW() WHERE id = v_activation.id;
        RETURN jsonb_build_object(
            'success', true, 
            'message', '授權有效',
            'already_activated', true
        );
    END IF;
    
    SELECT COUNT(*) INTO v_active_count 
    FROM activations 
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
        
        UPDATE activations SET is_active = false 
        WHERE license_id = v_license.id AND is_active = true;
        
        UPDATE licenses SET transfers_used = transfers_used + 1 
        WHERE id = v_license.id;
    END IF;
    
    INSERT INTO activations (license_id, machine_fingerprint)
    VALUES (v_license.id, p_machine_fingerprint);
    
    RETURN jsonb_build_object(
        'success', true, 
        'message', '授權成功！'
    );
END;
$$;

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
    SELECT * INTO v_license FROM licenses WHERE license_key = UPPER(p_license_key);
    
    IF v_license IS NULL THEN
        RETURN jsonb_build_object('success', false, 'message', '序號不存在');
    END IF;
    
    SELECT * INTO v_activation 
    FROM activations 
    WHERE license_id = v_license.id 
      AND machine_fingerprint = p_machine_fingerprint 
      AND is_active = true;
    
    IF v_activation IS NULL THEN
        RETURN jsonb_build_object('success', false, 'message', '此機器未授權');
    END IF;
    
    UPDATE activations SET last_verified_at = NOW() WHERE id = v_activation.id;
    
    RETURN jsonb_build_object(
        'success', true, 
        'message', '授權有效',
        'license_type', v_license.license_type,
        'activated_at', v_activation.activated_at
    );
END;
$$;

-- 完成！查看最終結果
SELECT '遷移完成！' as status, COUNT(*) as total_licenses FROM licenses;

-- （可選）確認無誤後刪除舊表
-- DROP TABLE licenses_old;
