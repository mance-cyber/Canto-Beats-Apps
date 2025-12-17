-- ==================== Canto-beats 有時限授權序號設定 ====================
-- 在 Supabase SQL Editor 執行此腳本
-- 到期時間從用戶首次啟用開始計算，而非 SQL 執行時間
-- 執行步驟：Dashboard > SQL Editor > New query > 貼上此內容 > Run

-- ============================================================
-- 步驟 1: 新增欄位
-- expires_at: 實際到期時間（首次啟用時設定）
-- validity_days: 有效天數（用於計算 expires_at）
-- ============================================================
ALTER TABLE app_licenses 
ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ;

ALTER TABLE app_licenses 
ADD COLUMN IF NOT EXISTS validity_days INTEGER;

-- ============================================================
-- 步驟 2: 更新 activate_license 函數
-- 首次啟用時，根據 validity_days 設定 expires_at
-- ============================================================
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
    
    -- 檢查是否已過期（只有當 expires_at 已設定時才檢查）
    IF v_license.expires_at IS NOT NULL AND v_license.expires_at < NOW() THEN
        RETURN jsonb_build_object(
            'success', false, 
            'message', '序號已過期',
            'expired', true,
            'expires_at', v_license.expires_at
        );
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
            'already_activated', true,
            'expires_at', v_license.expires_at
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
    ELSE
        -- ★ 首次啟用：如果有 validity_days 但 expires_at 未設定，現在設定它
        IF v_license.validity_days IS NOT NULL AND v_license.expires_at IS NULL THEN
            UPDATE app_licenses 
            SET expires_at = NOW() + (v_license.validity_days || ' days')::INTERVAL
            WHERE id = v_license.id;
            
            -- 重新讀取更新後的記錄
            SELECT * INTO v_license FROM app_licenses WHERE id = v_license.id;
        END IF;
    END IF;
    
    INSERT INTO app_activations (license_id, machine_fingerprint)
    VALUES (v_license.id, p_machine_fingerprint);
    
    RETURN jsonb_build_object(
        'success', true, 
        'message', '授權成功！',
        'expires_at', v_license.expires_at,
        'validity_days', v_license.validity_days
    );
END;
$$;

-- ============================================================
-- 步驟 3: 更新 verify_license 函數（加入到期檢查）
-- ============================================================
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
    
    -- 檢查是否已過期
    IF v_license.expires_at IS NOT NULL AND v_license.expires_at < NOW() THEN
        RETURN jsonb_build_object(
            'success', false, 
            'message', '序號已過期',
            'expired', true,
            'expires_at', v_license.expires_at
        );
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
        'activated_at', v_activation.activated_at,
        'expires_at', v_license.expires_at
    );
END;
$$;

-- ============================================================
-- 步驟 4: 插入 20 個有時限的序號（7 天有效期，從首次啟用開始）
-- validity_days = 7 表示有效期為 7 天
-- expires_at = NULL 表示尚未啟用，啟用時會自動設定
-- ============================================================
INSERT INTO app_licenses (license_key, license_type, transfers_allowed, validity_days, expires_at, notes) VALUES
('CANTO-7FFO-CJEB-AOBA-DMGY', 'permanent', 1, 7, NULL, '有時限授權 - 7天(從啟用開始)'),
('CANTO-QMTH-NN4B-G5ZX-YKYT', 'permanent', 1, 7, NULL, '有時限授權 - 7天(從啟用開始)'),
('CANTO-LXVJ-DVEB-JULY-TW6R', 'permanent', 1, 7, NULL, '有時限授權 - 7天(從啟用開始)'),
('CANTO-KTJF-KOMB-EJ7D-QOBM', 'permanent', 1, 7, NULL, '有時限授權 - 7天(從啟用開始)'),
('CANTO-LG3A-67UB-4WSX-OOQU', 'permanent', 1, 7, NULL, '有時限授權 - 7天(從啟用開始)'),
('CANTO-QGDR-YMMB-F4WA-UD7K', 'permanent', 1, 7, NULL, '有時限授權 - 7天(從啟用開始)'),
('CANTO-HKX6-4ZMB-HUKJ-WZRG', 'permanent', 1, 7, NULL, '有時限授權 - 7天(從啟用開始)'),
('CANTO-7ADY-MVMB-GYNL-LAI2', 'permanent', 1, 7, NULL, '有時限授權 - 7天(從啟用開始)'),
('CANTO-VCWW-EG4B-KN6K-PYT4', 'permanent', 1, 7, NULL, '有時限授權 - 7天(從啟用開始)'),
('CANTO-AOXX-XFUB-Q3QR-SLPP', 'permanent', 1, 7, NULL, '有時限授權 - 7天(從啟用開始)'),
('CANTO-KXWY-2X4B-VG7L-UQGL', 'permanent', 1, 7, NULL, '有時限授權 - 7天(從啟用開始)'),
('CANTO-DWWU-K34B-RWBO-QN6U', 'permanent', 1, 7, NULL, '有時限授權 - 7天(從啟用開始)'),
('CANTO-UHT5-TSUB-SUSB-N7QN', 'permanent', 1, 7, NULL, '有時限授權 - 7天(從啟用開始)'),
('CANTO-LD2Q-YH4B-2KJZ-6MIR', 'permanent', 1, 7, NULL, '有時限授權 - 7天(從啟用開始)'),
('CANTO-HCRW-ADMB-IDQI-YUXT', 'permanent', 1, 7, NULL, '有時限授權 - 7天(從啟用開始)'),
('CANTO-LJDB-GEMB-LZKG-GNQY', 'permanent', 1, 7, NULL, '有時限授權 - 7天(從啟用開始)'),
('CANTO-S4HR-UFUB-MHY6-7R4B', 'permanent', 1, 7, NULL, '有時限授權 - 7天(從啟用開始)'),
('CANTO-YPJG-ZG4B-A7PS-4GON', 'permanent', 1, 7, NULL, '有時限授權 - 7天(從啟用開始)'),
('CANTO-6BKB-2OUB-GXZT-ZQ3C', 'permanent', 1, 7, NULL, '有時限授權 - 7天(從啟用開始)'),
('CANTO-FQJZ-JNUB-XCP7-MPGV', 'permanent', 1, 7, NULL, '有時限授權 - 7天(從啟用開始)')
ON CONFLICT (license_key) DO NOTHING;

-- ============================================================
-- 驗證結果
-- ============================================================
SELECT 
    '設定完成！' as status, 
    COUNT(*) as total_time_limited_licenses
FROM app_licenses 
WHERE validity_days IS NOT NULL;

-- 查看序號狀態
SELECT 
    license_key,
    validity_days as "有效天數",
    expires_at as "到期時間",
    CASE 
        WHEN expires_at IS NULL THEN '未啟用'
        WHEN expires_at > NOW() THEN '有效'
        ELSE '已過期'
    END as "狀態"
FROM app_licenses 
WHERE validity_days IS NOT NULL
ORDER BY created_at DESC;
