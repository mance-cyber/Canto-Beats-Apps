"use client";

import { useRef, useEffect, useState } from "react";
import { Languages, Zap, FileText, Video } from "lucide-react";

const features = [
  {
    icon: Languages,
    title: "地道港式粵語",
    description: "唔係普通話轉譯，係真正聽得明「這裏」同「呢度」、「回家」同「返屋企」分別嘅 AI。",
  },
  {
    icon: Zap,
    title: "極速本地運算",
    description: "利用你電腦嘅 GPU/CPU 加速，唔洗 upload 片上雲端，私隱度極高，速度快 10 倍。",
  },
  {
    icon: FileText,
    title: "支援多種格式",
    description: "一鍵輸出 SRT, ASS, TXT。直接拖入 Premiere Pro, Final Cut, Davinci Resolve 即可使用。",
  },
];

export default function FeaturesSection() {
  const gridRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const grid = gridRef.current;
    if (!grid) return;

    const cards = grid.querySelectorAll<HTMLElement>(".feature-card");

    const handleMouseMove = (e: MouseEvent) => {
      cards.forEach((card) => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        // Update spotlight position
        const spotlightBg = card.querySelector<HTMLElement>(".spotlight-bg");
        if (spotlightBg) {
          spotlightBg.style.background = `radial-gradient(400px circle at ${x}px ${y}px, rgba(255, 84, 0, 0.15), transparent 40%)`;
          spotlightBg.style.opacity = "1";
        }
      });
    };

    const handleCardMouseMove = (e: MouseEvent, card: HTMLElement) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      const centerX = rect.width / 2;
      const centerY = rect.height / 2;

      const rotateX = ((y - centerY) / centerY) * -10;
      const rotateY = ((x - centerX) / centerX) * 10;

      card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
    };

    const handleCardMouseLeave = (card: HTMLElement) => {
      card.style.transform = "perspective(1000px) rotateX(0deg) rotateY(0deg)";
    };

    grid.addEventListener("mousemove", handleMouseMove);

    cards.forEach((card) => {
      card.addEventListener("mousemove", (e) => handleCardMouseMove(e, card));
      card.addEventListener("mouseleave", () => handleCardMouseLeave(card));
    });

    return () => {
      grid.removeEventListener("mousemove", handleMouseMove);
      cards.forEach((card) => {
        card.removeEventListener("mousemove", (e) => handleCardMouseMove(e, card));
        card.removeEventListener("mouseleave", () => handleCardMouseLeave(card));
      });
    };
  }, []);

  return (
    <section id="features" className="py-24 container mx-auto px-6" style={{ perspective: "1000px" }}>
      {/* Animation Block */}
      <div className="relative w-full max-w-2xl mx-auto h-48 mb-12 flex flex-col items-center justify-center select-none pointer-events-none">
        <div className="relative w-full flex items-center justify-center h-28">
          {/* Background Track */}
          <div className="absolute w-3/4 h-2 bg-slate-800 rounded-full overflow-hidden z-0 top-1/2 transform -translate-y-1/2">
            <div className="w-full h-full scrolling-gradient flow-line opacity-30" />
          </div>

          {/* Video Icon */}
          <div className="video-slide absolute z-10 flex flex-col items-center">
            <div className="w-16 h-16 bg-slate-700 rounded-xl border-2 border-slate-500 flex items-center justify-center text-slate-300 shadow-xl relative backdrop-blur-sm">
              <Video className="w-8 h-8" />
              <div className="absolute -top-2 -right-2 bg-blue-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full">
                MP4
              </div>
            </div>
          </div>

          {/* App Interface */}
          <div className="chip-pulse relative z-20 bg-slate-900 w-44 h-32 rounded-xl border-2 border-slate-600 flex flex-col shadow-2xl overflow-hidden">
            <div className="h-6 bg-slate-800 border-b border-slate-700 flex items-center px-3 gap-1.5 w-full">
              <div className="w-2.5 h-2.5 rounded-full bg-red-500" />
              <div className="w-2.5 h-2.5 rounded-full bg-yellow-500" />
              <div className="w-2.5 h-2.5 rounded-full bg-green-500" />
            </div>
            <div className="flex-1 relative w-full h-full bg-slate-900 flex flex-col items-center justify-center p-2">
              {/* Idle State */}
              <div className="idle-anim absolute inset-0 flex flex-col items-center justify-center gap-2">
                <div className="h-1.5 w-3/4 bg-slate-700 rounded-full" />
                <div className="h-1.5 w-1/2 bg-slate-700 rounded-full" />
                <div className="h-1.5 w-2/3 bg-slate-700 rounded-full" />
              </div>
              {/* Processing State */}
              <div className="processing-anim absolute inset-0 flex flex-col items-center justify-center gap-3">
                <div className="flex items-center justify-center gap-1 h-8">
                  <div className="wave-bar w-1 bg-primary rounded-full" style={{ animationDelay: "0s" }} />
                  <div className="wave-bar w-1 bg-primary rounded-full" style={{ animationDelay: "0.1s" }} />
                  <div className="wave-bar w-1 bg-primary rounded-full" style={{ animationDelay: "0.2s" }} />
                  <div className="wave-bar w-1 bg-primary rounded-full" style={{ animationDelay: "0.3s" }} />
                  <div className="wave-bar w-1 bg-primary rounded-full" style={{ animationDelay: "0.4s" }} />
                </div>
                <div className="flex flex-col gap-1.5 w-3/4 items-center">
                  <div className="w-full h-1.5 bg-slate-700 rounded-full overflow-hidden">
                    <div className="typing-bar h-full bg-primary" />
                  </div>
                  <div className="w-2/3 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                    <div className="typing-bar h-full bg-primary/70" style={{ animationDuration: "1.2s" }} />
                  </div>
                </div>
                <div className="absolute bottom-2 right-2 flex items-center gap-1">
                  <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-ping" />
                  <span className="text-[8px] text-green-500 font-mono">AI WORKING</span>
                </div>
              </div>
            </div>
          </div>

          {/* SRT Output */}
          <div className="srt-slide absolute z-10 flex flex-col items-center">
            <div className="w-16 h-16 bg-white rounded-xl border-2 border-primary flex items-center justify-center text-primary shadow-[0_0_20px_rgba(255,84,0,0.4)] relative">
              <FileText className="w-8 h-8" />
              <div className="absolute -top-2 -right-2 bg-primary text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full">
                SRT
              </div>
            </div>
          </div>
        </div>

        {/* Status Text */}
        <div className="mt-6 h-6 text-sm font-mono font-bold tracking-wider relative w-full text-center">
          <StatusText />
        </div>
      </div>

      <div ref={gridRef} className="grid md:grid-cols-3 gap-8 group/grid">
        {features.map((feature, index) => {
          const Icon = feature.icon;
          return (
            <div
              key={index}
              className="feature-card tilt-feature-card relative p-[1px] rounded-2xl overflow-hidden group"
            >
              {/* Spotlight background */}
              <div className="absolute inset-0 bg-gradient-to-r from-white/10 to-white/0 opacity-0 group-hover:opacity-100 transition duration-300 spotlight-bg" />

              {/* Card content */}
              <div className="relative h-full bg-card p-6 rounded-2xl border border-white/5 group-hover:border-transparent transition">
                <div className="w-12 h-12 bg-primary/20 rounded-lg flex items-center justify-center text-primary mb-4 group-hover:scale-110 transition duration-300">
                  <Icon className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
                <p className="text-slate-400">{feature.description}</p>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

// Status Text Component with animation using state
function StatusText() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setPhase((prev) => (prev + 1) % 3);
    }, 1333); // 4s / 3 phases

    return () => clearInterval(interval);
  }, []);

  const texts = [
    { text: "1. 拖入影片檔案...", color: "text-slate-400" },
    { text: "2. 生成器 AI 運算中...", color: "text-primary" },
    { text: "3. 成功匯出 SRT 字幕！", color: "text-green-400" },
  ];

  return (
    <div className={`${texts[phase].color} transition-colors duration-300`}>
      {texts[phase].text}
    </div>
  );
}
