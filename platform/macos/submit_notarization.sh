#!/bin/bash
# 公證提交腳本

echo "==================================="
echo "Canto-beats 公證提交"
echo "==================================="
echo ""
echo "請先生成 App-specific Password："
echo "1. 前往 https://appleid.apple.com"
echo "2. 登入 manhinli@gmail.com"
echo "3. 進入 Sign-In and Security → App-Specific Passwords"
echo "4. 生成新密碼（名稱：Canto-beats Notarization）"
echo ""
read -s -p "請輸入 App-specific password: " APP_PASS
echo ""
echo ""
echo "開始提交公證（預計 5-30 分鐘）..."
echo ""

xcrun notarytool submit dist/Canto-beats-macOS-Notarized.dmg \
  --apple-id "manhinli@gmail.com" \
  --team-id "678P6T2H5Q" \
  --password "$APP_PASS" \
  --wait

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 公證成功！"
    echo ""
    echo "開始裝訂公證票據..."
    
    # 裝訂 .app
    xcrun stapler staple dist/Canto-beats.app
    
    # 重新創建 DMG
    rm -rf dist/dmg_notarize_temp
    mkdir -p dist/dmg_notarize_temp
    cp -R dist/Canto-beats.app dist/dmg_notarize_temp/
    ln -s /Applications dist/dmg_notarize_temp/Applications
    
    cat > dist/dmg_notarize_temp/使用說明.txt << 'EOF'
📦 Canto-beats 安裝說明

⚠️ 重要: 請將 Canto-beats.app 拖動到 Applications (應用程式) 資料夾中安裝

為什麼？
- MLX GPU 加速需要可寫入的目錄
- 從 DMG 直接執行會使用 CPU 模式 (慢)
- 安裝到 Applications 後會使用 GPU 加速 (快 5-10 倍)

步驟:
1. 將 Canto-beats.app 拖到 Applications 資料夾
2. 從 Applications 資料夾啟動程式
3. 享受流暢的 GPU 加速轉譯！
EOF
    
    rm -f dist/Canto-beats-macOS-Notarized.dmg
    hdiutil create -volname Canto-beats \
      -srcfolder dist/dmg_notarize_temp \
      -ov -format UDZO \
      dist/Canto-beats-macOS-Notarized.dmg
    
    rm -rf dist/dmg_notarize_temp
    
    # 裝訂 DMG
    xcrun stapler staple dist/Canto-beats-macOS-Notarized.dmg
    
    echo ""
    echo "✅ 裝訂完成！"
    echo ""
    echo "最終產物："
    echo "  dist/Canto-beats-macOS-Notarized.dmg"
    echo ""
    echo "驗證："
    spctl -a -v dist/Canto-beats.app
    
else
    echo ""
    echo "❌ 公證失敗"
    echo "請檢查 App-specific password 是否正確"
fi
