"use client";

import { Mail, MessageSquare, Clock } from "lucide-react";
import Link from "next/link";
import Image from "next/image";

export default function ContactPage() {
  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <nav className="sticky top-0 z-50 w-full bg-[#0F172A]/80 backdrop-blur-md border-b border-white/5">
        <div className="container mx-auto px-6 py-4 flex justify-between items-center">
          <Link href="/" className="flex items-center gap-2">
            <Image src="/app icon_002.png" alt="Canto-Beats" width={32} height={32} />
            <span className="text-xl font-bold tracking-tight">Canto-Beats</span>
          </Link>
          <Link
            href="/"
            className="text-slate-300 hover:text-primary transition"
          >
            返回主頁
          </Link>
        </div>
      </nav>

      {/* Main Content */}
      <div className="container mx-auto px-6 py-20">
        <div className="max-w-3xl mx-auto">
          {/* Page Title */}
          <div className="text-center mb-16">
            <h1 className="text-4xl md:text-5xl font-black mb-4">
              聯絡我們
            </h1>
            <p className="text-xl text-slate-400">
              有任何問題或建議？我們很樂意聽取你的意見
            </p>
          </div>

          {/* Contact Cards */}
          <div className="grid md:grid-cols-2 gap-6 mb-12">
            {/* Email */}
            <div className="bg-slate-800/50 p-8 rounded-2xl border border-slate-700 hover:border-primary/50 transition">
              <div className="bg-primary/10 w-14 h-14 rounded-xl flex items-center justify-center mb-4">
                <Mail className="w-7 h-7 text-primary" />
              </div>
              <h3 className="text-xl font-bold mb-2">電郵查詢</h3>
              <p className="text-slate-400 text-sm mb-4">
                我們會在 24 小時內回覆
              </p>
              <a
                href="mailto:info@cantobeats.com"
                className="text-primary hover:text-primary-hover font-medium transition"
              >
                info@cantobeats.com
              </a>
            </div>

            {/* Support Hours */}
            <div className="bg-slate-800/50 p-8 rounded-2xl border border-slate-700">
              <div className="bg-primary/10 w-14 h-14 rounded-xl flex items-center justify-center mb-4">
                <Clock className="w-7 h-7 text-primary" />
              </div>
              <h3 className="text-xl font-bold mb-2">支援時間</h3>
              <p className="text-slate-400 text-sm mb-4">
                香港時間
              </p>
              <p className="text-slate-300">
                週一至週五<br />
                上午 10:00 - 下午 6:00
              </p>
            </div>
          </div>

          {/* FAQ Section */}
          <div className="bg-gradient-to-b from-slate-800 to-slate-900 p-8 md:p-12 rounded-2xl border border-slate-700">
            <div className="flex items-center gap-3 mb-6">
              <MessageSquare className="w-6 h-6 text-primary" />
              <h2 className="text-2xl font-bold">常見問題</h2>
            </div>

            <div className="space-y-6">
              <div>
                <h3 className="font-bold text-lg mb-2">如何獲取授權序號？</h3>
                <p className="text-slate-400">
                  完成付款後，授權序號會立即發送到你的電郵。請檢查垃圾郵件夾，如果沒有收到請聯絡我們。
                </p>
              </div>

              <div>
                <h3 className="font-bold text-lg mb-2">可以退款嗎？</h3>
                <p className="text-slate-400">
                  如果對軟件不滿意，可以在購買後 30 天內申請全額退款。
                </p>
              </div>

              <div>
                <h3 className="font-bold text-lg mb-2">支援哪些付款方式？</h3>
                <p className="text-slate-400">
                  我們支援 Visa、Mastercard、AlipayHK 和 WeChat Pay。
                </p>
              </div>

              <div>
                <h3 className="font-bold text-lg mb-2">序號可以用在幾部電腦？</h3>
                <p className="text-slate-400">
                  每個序號可以在最多 3 部裝置上啟用使用。
                </p>
              </div>

              <div>
                <h3 className="font-bold text-lg mb-2">技術支援</h3>
                <p className="text-slate-400">
                  如遇到技術問題，請將問題詳情和截圖發送到 info@cantobeats.com，我們會盡快協助你解決。
                </p>
              </div>
            </div>
          </div>

          {/* CTA */}
          <div className="text-center mt-12">
            <p className="text-slate-400 mb-6">
              還沒試用過？
            </p>
            <Link
              href="/#pricing"
              className="inline-block bg-primary hover:bg-primary-hover text-white px-8 py-4 rounded-xl font-bold text-lg transition transform hover:-translate-y-1 shadow-lg"
            >
              立即購買
            </Link>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-12 text-center text-slate-500">
        <div className="container mx-auto px-6">
          <div className="flex items-center justify-center gap-2 mb-4 text-slate-300">
            <Image src="/app icon_002.png" alt="Canto-Beats" width={24} height={24} />
            <span className="font-bold text-lg">Canto-Beats</span>
          </div>
          <p>Designed & Made in Hong Kong 🇭🇰</p>
          <p className="mt-4 text-xs">
            © {new Date().getFullYear()} Canto-Beats. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
