-- Supabase 監控與警報設置
-- 在 Supabase SQL Editor 中執行此腳本

-- ============================================
-- 1. 創建監控函數
-- ============================================

-- 函數：檢查授權序號庫存並觸發警報
CREATE OR REPLACE FUNCTION check_license_inventory()
RETURNS trigger AS $$
DECLARE
  available_count INTEGER;
  threshold INTEGER := 100;
BEGIN
  -- 計算可用序號數量
  SELECT COUNT(*) INTO available_count
  FROM licenses
  WHERE is_used = false;

  -- 如果庫存低於警戒線，記錄警告
  IF available_count < threshold THEN
    RAISE WARNING 'Low license inventory: % licenses remaining (threshold: %)',
      available_count, threshold;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 2. 創建觸發器
-- ============================================

-- 當授權序號被標記為已使用時，自動檢查庫存
DROP TRIGGER IF EXISTS trigger_check_license_inventory ON licenses;

CREATE TRIGGER trigger_check_license_inventory
  AFTER UPDATE OF is_used ON licenses
  FOR EACH ROW
  WHEN (NEW.is_used = true AND OLD.is_used = false)
  EXECUTE FUNCTION check_license_inventory();

-- ============================================
-- 3. 創建監控視圖（方便查詢）
-- ============================================

-- 視圖：授權序號統計
CREATE OR REPLACE VIEW license_stats AS
SELECT
  COUNT(*) as total_licenses,
  COUNT(*) FILTER (WHERE is_used = true) as used_licenses,
  COUNT(*) FILTER (WHERE is_used = false) as available_licenses,
  ROUND(
    100.0 * COUNT(*) FILTER (WHERE is_used = true) / NULLIF(COUNT(*), 0),
    2
  ) as usage_percentage
FROM licenses;

-- 視圖：每日購買統計
CREATE OR REPLACE VIEW daily_purchase_stats AS
SELECT
  DATE(created_at) as purchase_date,
  COUNT(*) as purchase_count,
  SUM(amount) as total_revenue,
  COUNT(DISTINCT customer_email) as unique_customers
FROM purchases
GROUP BY DATE(created_at)
ORDER BY purchase_date DESC;

-- 視圖：最近7天統計
CREATE OR REPLACE VIEW recent_stats AS
SELECT
  'Last 24 hours' as period,
  COUNT(*) as purchases,
  SUM(amount) as revenue
FROM purchases
WHERE created_at > NOW() - INTERVAL '24 hours'
UNION ALL
SELECT
  'Last 7 days' as period,
  COUNT(*) as purchases,
  SUM(amount) as revenue
FROM purchases
WHERE created_at > NOW() - INTERVAL '7 days'
UNION ALL
SELECT
  'Last 30 days' as period,
  COUNT(*) as purchases,
  SUM(amount) as revenue
FROM purchases
WHERE created_at > NOW() - INTERVAL '30 days';

-- ============================================
-- 4. 創建警報記錄表（可選）
-- ============================================

-- 表：記錄所有警報事件
CREATE TABLE IF NOT EXISTS alert_logs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  alert_type VARCHAR(50) NOT NULL,
  severity VARCHAR(20) NOT NULL, -- 'info', 'warning', 'critical'
  message TEXT NOT NULL,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引：按時間和類型查詢
CREATE INDEX IF NOT EXISTS idx_alert_logs_created_at ON alert_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alert_logs_type ON alert_logs(alert_type);

-- 函數：記錄警報
CREATE OR REPLACE FUNCTION log_alert(
  p_alert_type VARCHAR,
  p_severity VARCHAR,
  p_message TEXT,
  p_metadata JSONB DEFAULT '{}'::jsonb
)
RETURNS UUID AS $$
DECLARE
  alert_id UUID;
BEGIN
  INSERT INTO alert_logs (alert_type, severity, message, metadata)
  VALUES (p_alert_type, p_severity, p_message, p_metadata)
  RETURNING id INTO alert_id;

  RETURN alert_id;
END;
$$ LANGUAGE plpgsql;

-- 更新監控函數以記錄警報
CREATE OR REPLACE FUNCTION check_license_inventory()
RETURNS trigger AS $$
DECLARE
  available_count INTEGER;
  threshold INTEGER := 100;
  alert_id UUID;
BEGIN
  -- 計算可用序號數量
  SELECT COUNT(*) INTO available_count
  FROM licenses
  WHERE is_used = false;

  -- 如果庫存低於警戒線
  IF available_count < threshold THEN
    -- 記錄警報
    SELECT log_alert(
      'low_license_inventory',
      'warning',
      format('Low license inventory: %s licenses remaining (threshold: %s)',
        available_count, threshold),
      jsonb_build_object(
        'available_licenses', available_count,
        'threshold', threshold,
        'triggered_by_license', NEW.license_key
      )
    ) INTO alert_id;

    RAISE WARNING 'Low license inventory: % licenses remaining (Alert ID: %)',
      available_count, alert_id;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 5. 啟用 RLS (如果尚未啟用)
-- ============================================

ALTER TABLE alert_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role only" ON alert_logs
  FOR ALL
  USING (auth.role() = 'service_role');

-- ============================================
-- 6. 實用查詢範例
-- ============================================

-- 查詢當前授權序號統計
-- SELECT * FROM license_stats;

-- 查詢每日購買統計
-- SELECT * FROM daily_purchase_stats LIMIT 30;

-- 查詢最近7天統計
-- SELECT * FROM recent_stats;

-- 查詢最近的警報
-- SELECT * FROM alert_logs ORDER BY created_at DESC LIMIT 10;

-- 查詢低庫存警報
-- SELECT * FROM alert_logs
-- WHERE alert_type = 'low_license_inventory'
-- ORDER BY created_at DESC;

-- 手動觸發庫存檢查（測試用）
-- SELECT check_license_inventory() FROM licenses WHERE is_used = true LIMIT 1;

-- ============================================
-- 7. 清理過期警報（可選）
-- ============================================

-- 函數：清理30天前的警報記錄
CREATE OR REPLACE FUNCTION cleanup_old_alerts()
RETURNS INTEGER AS $$
DECLARE
  deleted_count INTEGER;
BEGIN
  DELETE FROM alert_logs
  WHERE created_at < NOW() - INTERVAL '30 days';

  GET DIAGNOSTICS deleted_count = ROW_COUNT;
  RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- 可以使用 pg_cron 擴展來定期執行清理
-- 或手動執行: SELECT cleanup_old_alerts();

-- ============================================
-- 完成！
-- ============================================

-- 驗證安裝
SELECT
  'Monitoring setup complete!' as status,
  (SELECT COUNT(*) FROM license_stats) as stats_available,
  (SELECT COUNT(*) FROM alert_logs) as alert_logs_ready;
