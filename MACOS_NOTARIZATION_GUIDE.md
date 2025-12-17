# macOS 公证 (Notarization) 完整指南

为 Canto-beats 配置 Apple 公证，消除用户安装时的安全警告。

---

## 前提条件

| 需求 | 说明 |
|------|------|
| **Apple Developer Program** | 付费会员 ($99/年) |
| **Developer ID Application 证书** | 从 Apple Developer Portal 获取 |
| **App-Specific Password** | 从 [appleid.apple.com](https://appleid.apple.com) 创建 |
| **macOS + Xcode CLI** | `xcode-select --install` |

---

## 快速开始

### 1. 设置环境变量

```bash
export APPLE_ID="your@email.com"
export TEAM_ID="ABCD1234EF"              # 10 位 Team ID
export APP_PASSWORD="xxxx-xxxx-xxxx-xxxx" # App-Specific Password
export SIGNING_IDENTITY="Developer ID Application: Your Name (TEAM_ID)"
```

### 2. 构建应用

```bash
python build_silicon_macos.py
```

### 3. 签名并公证

```bash
python notarize_macos.py
```

完成后，`dist/Canto-beats-macOS-Notarized.dmg` 可直接分发。

---

## 获取证书

### Step 1: 加入 Apple Developer Program

1. 访问 [developer.apple.com](https://developer.apple.com)
2. 注册并支付年费 ($99)
3. 等待审核通过 (通常 24-48 小时)

### Step 2: 创建 Developer ID 证书

1. 打开 **Keychain Access** (钥匙串访问)
2. 菜单 → **证书助理** → **从证书颁发机构请求证书**
3. 填写邮箱，选择"存储到磁盘"
4. 登录 [Apple Developer Portal](https://developer.apple.com/account)
5. **Certificates** → **+** → **Developer ID Application**
6. 上传 CSR 文件，下载证书
7. 双击安装到钥匙串

### Step 3: 创建 App-Specific Password

1. 访问 [appleid.apple.com](https://appleid.apple.com)
2. 登录 → **安全** → **App 专用密码**
3. 点击 **生成密码**
4. 保存生成的密码 (格式: `xxxx-xxxx-xxxx-xxxx`)

---

## 手动流程 (不使用脚本)

### 1. 签名

```bash
# 签名 .app
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: Your Name (TEAM_ID)" \
  --options runtime \
  --entitlements entitlements.plist \
  dist/Canto-beats.app
```

### 2. 创建 DMG

```bash
mkdir -p dist/dmg
cp -r dist/Canto-beats.app dist/dmg/
ln -s /Applications dist/dmg/Applications

hdiutil create -volname "Canto-beats" \
  -srcfolder dist/dmg -ov -format UDZO \
  dist/Canto-beats.dmg

codesign --sign "Developer ID Application: Your Name (TEAM_ID)" \
  dist/Canto-beats.dmg

rm -rf dist/dmg
```

### 3. 提交公证

```bash
xcrun notarytool submit dist/Canto-beats.dmg \
  --apple-id "your@email.com" \
  --team-id "TEAM_ID" \
  --password "app-specific-password" \
  --wait
```

### 4. 装订票据

```bash
xcrun stapler staple dist/Canto-beats.app
xcrun stapler staple dist/Canto-beats.dmg
```

### 5. 验证

```bash
spctl --assess --verbose dist/Canto-beats.app
# 预期: accepted
```

---

## GitHub Actions 自动化

### 设置 Secrets

在仓库 **Settings** → **Secrets and variables** → **Actions** 添加:

| Secret 名称 | 说明 |
|-------------|------|
| `APPLE_ID` | Apple ID 邮箱 |
| `APPLE_TEAM_ID` | Team ID |
| `APPLE_APP_PASSWORD` | App-Specific Password |
| `MACOS_CERTIFICATE` | 证书 Base64 编码 |
| `MACOS_CERTIFICATE_PWD` | 证书密码 |

### 导出证书 (Base64)

```bash
# 从钥匙串导出 .p12 文件，然后:
base64 -i certificate.p12 | pbcopy
```

### Workflow 配置

在 `.github/workflows/build-macos.yml` 添加:

```yaml
- name: Import Certificate
  env:
    CERTIFICATE_BASE64: ${{ secrets.MACOS_CERTIFICATE }}
    CERTIFICATE_PWD: ${{ secrets.MACOS_CERTIFICATE_PWD }}
  run: |
    echo $CERTIFICATE_BASE64 | base64 --decode > certificate.p12
    security create-keychain -p "" build.keychain
    security default-keychain -s build.keychain
    security unlock-keychain -p "" build.keychain
    security import certificate.p12 -k build.keychain \
      -P "$CERTIFICATE_PWD" -T /usr/bin/codesign
    security set-key-partition-list -S apple-tool:,apple: \
      -s -k "" build.keychain

- name: Notarize
  env:
    APPLE_ID: ${{ secrets.APPLE_ID }}
    TEAM_ID: ${{ secrets.APPLE_TEAM_ID }}
    APP_PASSWORD: ${{ secrets.APPLE_APP_PASSWORD }}
    SIGNING_IDENTITY: "Developer ID Application: ..."
  run: python notarize_macos.py
```

---

## 常见问题

### "errSecInternalComponent" 错误

**原因**: 钥匙串权限问题

```bash
security unlock-keychain -p "" ~/Library/Keychains/login.keychain-db
```

### "The signature is invalid" 错误

**原因**: 二进制未正确签名

```bash
# 检查哪些文件未签名
codesign --verify --deep --verbose dist/Canto-beats.app 2>&1 | grep "invalid"
```

### 公证超时

**原因**: Apple 服务器繁忙

```bash
# 查询状态
xcrun notarytool history --apple-id EMAIL --team-id TEAM --password PWD
```

---

## 文件清单

| 文件 | 用途 |
|------|------|
| `entitlements.plist` | Hardened Runtime 权限 |
| `notarize_macos.py` | 自动化公证脚本 |
| `build_silicon_macos.py` | 构建 .app |
