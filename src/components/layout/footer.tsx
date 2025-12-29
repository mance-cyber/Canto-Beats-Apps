"use client";

import { useState } from "react";
import Link from "next/link";
import { X } from "lucide-react";
import Image from "next/image";

const privacyContent = `私隱政策

最後更新日期：2024 年 1 月

本私隱政策適用於 Canto-Beats 廣東話字幕生成器及其相關網站及服務（下稱「本服務」）。我們非常重視您的個人資料及私隱，並承諾按照本政策處理及保護您的資料。

1. 我們收集的資料

聯絡資料
• 電郵地址（購買及技術支援用）

使用情況資料（非必然會有）
• 若您瀏覽我們的網站，我們可能透過 Cookies 及分析工具收集匿名統計資料，例如瀏覽頁面、停留時間、裝置類型等。
• 此等資料不會用作識別個別用戶身份。

不會收集的資料
• 您於本地電腦內處理的影片、音訊及字幕內容，完全不會上傳至我們的伺服器。
• 我們亦不會於本服務中讀取、儲存或分析您的影片內容。

2. 我們如何使用您的資料

我們只會將收集到的電郵地址用於以下用途：
• 發送購買確認及軟件下載／啟用資訊
• 提供重要軟件更新或服務變更通知
• 回覆您的查詢及提供技術支援
• 如您同意，發送與本服務相關的最新消息或優惠資訊（您可隨時取消訂閱）

我們不會出售、出租或與第三方分享您的個人資料作行銷用途。

3. 資料儲存及付款安全

付款資料
• 我們使用第三方支付服務商 Stripe 處理所有線上付款。
• 您的信用卡及付款資料由 Stripe 以其安全標準加密處理及儲存，我們無法接觸及不會儲存任何完整信用卡資料。

聯絡資料儲存
• 您的電郵地址會安全地儲存在我們的系統中，只供上述用途。
• 我們會在提供服務所需期間內保留資料，並依據法律／會計要求保存相關交易記錄。

4. 第三方服務

我們可能會使用以下第三方服務來營運及優化本服務：
• Stripe – 處理付款交易及相關風險管理
• Google Analytics – 網站流量及使用情況分析（以匿名或匿名化形式收集統計資料）

這些第三方服務會按照其各自的私隱政策處理資料。建議您同時參閱相關服務的私隱政策。

5. 資料安全

我們採用業界標準的技術及程序（包括加密及權限控制）保護您的個人資料，防止未經授權的存取、使用或披露。

雖然我們盡力保護資料，但互聯網傳輸並非百分百安全，我們無法保證絕對安全性。

6. 您的權利

如適用法律允許，您有權：
• 查詢我們是否持有您的個人資料
• 要求更正或更新不正確的資料
• 要求刪除或停止使用您的個人資料（但某些交易／會計記錄可能需按法律要求保留）
• 取消訂閱任何市場推廣電郵

如欲行使以上權利，請與我們聯絡。

7. 私隱政策更新

我們可能不時更新本私隱政策，以反映服務或法例要求的變更。
更新後的版本將刊載於我們的網站並標明「最後更新日期」，除非另有說明，更新將於刊登時立即生效。

8. 聯絡我們

如對本私隱政策或您的個人資料處理方式有任何疑問，請聯絡我們：

電郵： info@cantobeats.com
`;

const termsContent = `使用條款

最後更新日期：2025年 12月

本使用條款（下稱「本條款」）適用於 Canto-Beats 廣東話字幕生成器及其相關服務（下稱「本軟件」）。使用或安裝本軟件即表示你已閱讀、明白並同意受本條款約束。

1. 服務說明

1.1 本軟件為一款於用戶本地電腦運行的粵語自動字幕生成工具，可將音訊／影片中的語音轉換為文字字幕。
1.2 本軟件僅提供技術工具，本公司不參與或控制你所處理之任何影音內容。

2. 授權條款

2.1 在完成付款後，你將獲得一個非獨家、不可轉讓、不可再授權之永久使用授權。
2.2 除非另有書面約定，本授權僅供你本人或你的公司內部使用，不得轉售、出租、出借、轉讓或以任何形式提供予第三方作獨立使用。
2.3 每一份授權可安裝及啟用於最多三（3）部由你擁有或控制的裝置上。
2.4 在遵守適用法律的前提下，你可以使用本軟件處理個人或商業用途的影音內容，但其合法性及版權責任由你自行承擔。

3. 退款政策

3.1 自完成購買之日起 30 天內，如你對本軟件不滿意，可透過官方支援渠道申請全額退款。
3.2 退款獲批後：
• 相關授權將被視為立即終止；
• 你須停止使用本軟件，並自所有裝置中移除及卸載。

4. 使用規範

4.1 你同意不會利用本軟件從事任何違反適用法律或侵犯他人權益的行為，包括但不限於：
• 侵害著作權、商標權或其他智慧財產權之內容製作或散佈；
• 製作、傳播違法或具誹謗、仇恨、暴力、色情等不當內容；
• 嘗試入侵、破解或破壞本軟件或相關系統之安全。

4.2 除法律明確允許外，你不得：
• 對本軟件進行反向工程、反編譯或反組譯；
• 修改、拆分或基於本軟件製作衍生產品；
• 移除或更改本軟件上的任何版權或權利聲明。

5. 更新與支援政策

5.1 如你購買的方案標示包含「終身更新」，則在該方案有效期間內，你可免費獲得本軟件之功能改良、錯誤修正或相同產品線下的日後版本更新。
5.2 我們保留隨時調整未來版本價格、功能或發佈新產品（需另行購買）的權利。
5.3 技術支援服務之形式及回覆時間，將以我們當時公布之政策為準。

6. 免責聲明

6.1 本軟件按「現狀（as is）」提供，我們不保證：
• 生成字幕的內容在任何情況下均達到 100% 準確或無錯誤；
• 本軟件與所有硬件、系統或第三方軟件完全相容；
• 本軟件在任何時間均不會中斷、延遲或出現故障。

6.2 使用本軟件生成之字幕、文字或任何輸出內容，均由你自行判斷及使用，你須自行負責其準確性、合法性及合約／商業風險。

6.3 在適用法律允許的最大範圍內，我們不就因使用或無法使用本軟件而引致的任何直接、間接、附帶、衍生或懲罰性損失承擔責任。

7. 智慧財產權

7.1 本軟件及其所有相關程式碼、設計、介面、標誌、文件及技術之著作權及其他智慧財產權，均屬本公司或其授權人所有。
7.2 使用本軟件並不表示該等權利已被出售或轉移予你，你僅獲得依本條款使用本軟件的授權。

8. 條款修改

8.1 我們保留隨時修訂本條款的權利。更新後的版本將刊登於官方網站或軟件相關頁面，並標示最新更新日期。
8.2 除非法律另有規定，修訂於公布時即生效。如你在條款更新後仍繼續使用本軟件，即視為你已接受更新後的條款。

9. 適用法律及爭議解決

如無特別約定，本條款受香港特別行政區法律管轄並按其詮釋。因本條款或本軟件引起之任何爭議，雙方應先友好協商解決，如協商不成，則提交香港具管轄權的法院處理。
`;

export default function Footer() {
  const [modalOpen, setModalOpen] = useState<"privacy" | "terms" | null>(null);

  return (
    <>
      <footer id="footer" className="border-t border-slate-800 py-12 text-center text-slate-500">
        <div className="container mx-auto px-6">
          <div className="flex items-center justify-center gap-2 mb-4 text-slate-300">
            <Image src="/app icon_002.png" alt="Canto-Beats" width={24} height={24} />
            <span className="font-bold text-lg">Canto-Beats</span>
          </div>

          <p className="mb-4">Designed & Made in Hong Kong 🇭🇰</p>

          <div className="flex justify-center gap-6 text-sm">
            <button
              onClick={() => setModalOpen("privacy")}
              className="hover:text-primary transition"
            >
              私隱條款
            </button>
            <button
              onClick={() => setModalOpen("terms")}
              className="hover:text-primary transition"
            >
              使用條款
            </button>
            <Link href="#" className="hover:text-primary transition">
              聯絡我們
            </Link>
          </div>

          <p className="mt-8 text-xs">
            © {new Date().getFullYear()} 粵語自動字幕生成器. All rights reserved.
          </p>
        </div>
      </footer>

      {/* Modal */}
      {modalOpen && (
        <div
          className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={() => setModalOpen(null)}
        >
          <div
            className="bg-slate-900 border border-slate-700 rounded-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-slate-700">
              <h2 className="text-xl font-bold text-white">
                {modalOpen === "privacy" ? "私隱條款" : "使用條款"}
              </h2>
              <button
                onClick={() => setModalOpen(null)}
                className="text-slate-400 hover:text-white transition p-1"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            {/* Content */}
            <div className="p-6 overflow-y-auto max-h-[60vh]">
              <pre className="text-slate-300 text-sm whitespace-pre-wrap font-sans leading-relaxed">
                {modalOpen === "privacy" ? privacyContent : termsContent}
              </pre>
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-slate-700 flex justify-end">
              <button
                onClick={() => setModalOpen(null)}
                className="bg-primary hover:bg-primary-hover text-white px-6 py-2 rounded-lg font-medium transition"
              >
                關閉
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
