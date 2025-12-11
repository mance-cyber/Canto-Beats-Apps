"use client";

import { Monitor, Apple } from "lucide-react";

const platforms = [
  {
    name: "Windows",
    icon: Monitor,
    description: "Windows 10 / 11 (64-bit)",
    buttonText: "下載 .exe",
    animationClass: "float-slow",
    comingSoon: false,
  },
  {
    name: "macOS",
    icon: Apple,
    description: "Intel & Apple Silicon (M1/M2/M3)",
    buttonText: "即將推出",
    animationClass: "float-slow-delayed",
    comingSoon: true,
  },
];

export default function DownloadSection() {
  const handleDownload = (os: string) => {
    alert(`正在開始下載 ${os.toUpperCase()} 版本...\n\n(這只是一個演示頁面，實際下載鏈接會在此處觸發)`);
  };

  return (
    <section id="download" className="py-20 bg-slate-900">
      <div className="container mx-auto px-6 text-center">
        <h2 className="text-3xl font-bold mb-12">支援所有主流平台</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-2xl mx-auto">
          {platforms.map((platform) => {
            const Icon = platform.icon;
            return (
              <div
                key={platform.name}
                className="bg-card p-8 rounded-2xl border border-slate-700 hover:border-primary transition duration-500 relative overflow-hidden group hover:-translate-y-2"
              >
                <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition" />

                <div className={`${platform.animationClass} group-hover:scale-110 transition duration-500`}>
                  <Icon className="w-12 h-12 mx-auto mb-4 text-slate-300 group-hover:text-primary transition" />
                </div>

                <h3 className="text-xl font-bold group-hover:text-primary transition">
                  {platform.name}
                </h3>
                <p className="text-slate-400 text-sm mb-6">{platform.description}</p>

                <button
                  onClick={() => !platform.comingSoon && handleDownload(platform.name)}
                  disabled={platform.comingSoon}
                  className={`w-full py-3 rounded-lg font-medium transition ${
                    platform.comingSoon
                      ? "bg-slate-600 text-slate-400 cursor-not-allowed"
                      : "bg-slate-700 hover:bg-primary text-white"
                  }`}
                >
                  {platform.buttonText}
                </button>
              </div>
            );
          })}
        </div>

        <p className="mt-8 text-slate-500 text-sm">
          * 免費下載安裝，需購買激活碼解鎖匯出功能。
        </p>
      </div>
    </section>
  );
}
