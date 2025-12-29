"use client";

import { useEffect, useRef, useState } from "react";
import {
  X,
  ServerOff,
  Clock,
  Check,
  ShieldCheck,
  Coins,
  Frown,
  Smile,
  Sparkles,
} from "lucide-react";

function CountUp({ target, isVisible }: { target: number; isVisible: boolean }) {
  const [value, setValue] = useState(0);
  const hasAnimated = useRef(false);
  const isFloat = target % 1 !== 0;

  useEffect(() => {
    if (!isVisible || hasAnimated.current) return;
    hasAnimated.current = true;

    const duration = 2000;
    const startTime = performance.now();
    let animationId: number;

    function update(currentTime: number) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const ease = 1 - Math.pow(1 - progress, 4);

      const current = target * ease;
      setValue(isFloat ? parseFloat(current.toFixed(1)) : Math.floor(current));

      if (progress < 1) {
        animationId = requestAnimationFrame(update);
      } else {
        setValue(target);
      }
    }

    animationId = requestAnimationFrame(update);

    return () => {
      if (animationId) cancelAnimationFrame(animationId);
    };
  }, [target, isVisible]);

  // Use fixed width to prevent layout shift
  const displayValue = isFloat ? value.toFixed(1) : value.toString();
  const width = isFloat ? "4ch" : "2ch";

  return (
    <span
      className="inline-block text-right tabular-nums"
      style={{ minWidth: width }}
    >
      {displayValue}
    </span>
  );
}

export default function ComparisonSection() {
  const sectionRef = useRef<HTMLElement>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsVisible(true);
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.3 }
    );

    if (sectionRef.current) {
      observer.observe(sectionRef.current);
    }

    return () => observer.disconnect();
  }, []);

  return (
    <section
      ref={sectionRef}
      id="comparison"
      className="py-24 bg-slate-900 relative overflow-hidden"
    >
      {/* Background Elements */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden opacity-30 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-red-500/10 rounded-full blur-[100px]" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-primary/10 rounded-full blur-[100px]" />
      </div>

      <div className="container mx-auto px-6 relative z-10">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-black mb-6 leading-tight">
            <span className="text-slate-500 line-through decoration-red-500 decoration-4 text-2xl md:text-4xl block mb-2">
              外國 AI 識別率 <span className="text-red-500"><CountUp target={47} isVisible={isVisible} /></span>%
            </span>
            <span className="text-white text-4xl md:text-6xl drop-shadow-2xl">
              香港人 AI{" "}
              <span className="text-primary bg-clip-text text-transparent bg-gradient-to-r from-primary to-orange-400">
                <CountUp target={99.9} isVisible={isVisible} />% 準確
              </span>
            </span>
          </h2>
          <p className="text-xl text-slate-300 mt-4">
            你揀邊個？唔好再用「半桶水」嘅工具虐待自己。
          </p>
        </div>

        {/* Comparison Cards */}
        <div className="relative max-w-6xl mx-auto">
          {/* VS Badge */}
          <div className="hidden md:flex absolute left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 z-20 w-16 h-16 bg-slate-800 rounded-full border-4 border-slate-900 items-center justify-center shadow-2xl">
            <span className="font-black text-xl italic text-slate-500">VS</span>
          </div>

          <div className="grid md:grid-cols-2 gap-8 items-center">
            {/* Competitors Card */}
            <div className="group bg-slate-800/50 backdrop-blur-sm p-8 rounded-3xl border border-red-500/10 hover:border-red-500/30 transition-all duration-300 hover:shadow-[0_0_30px_rgba(239,68,68,0.1)] relative overflow-hidden">
              <div className="absolute -right-20 -top-20 w-64 h-64 bg-red-500/5 rounded-full blur-3xl group-hover:bg-red-500/10 transition" />

              <div className="flex justify-between items-center mb-8">
                <span className="bg-red-500/10 text-red-400 px-4 py-1.5 rounded-full font-bold text-sm border border-red-500/20">
                  傳統 / 其他對手
                </span>
                <Frown className="w-8 h-8 text-red-500/50" />
              </div>

              {/* Progress Bar */}
              <div className="mb-8 bg-slate-900/50 p-4 rounded-xl border border-red-500/10">
                <div className="flex justify-between text-xs text-red-300 mb-2 font-mono">
                  <span>識別準確率</span>
                  <span>47%</span>
                </div>
                <div className="w-full bg-slate-700/50 h-3 rounded-full overflow-hidden">
                  <div className="bg-red-500 h-full rounded-full w-[47%]" />
                </div>
                <p className="text-xs text-red-400/70 mt-2 text-right">
                  錯漏百出，要人手改餐死
                </p>
              </div>

              <ul className="space-y-6 relative z-10">
                <li className="flex gap-4 items-start opacity-80 group-hover:opacity-100 transition">
                  <X className="w-5 h-5 text-red-500 mt-1" />
                  <div>
                    <h4 className="font-bold text-lg text-slate-200 mb-1">YouTube 自動字幕</h4>
                    <p className="text-slate-400 text-sm">外國 AI 將『係咪』聽成『是咩』，睇到想死。</p>
                  </div>
                </li>
                <li className="flex gap-4 items-start opacity-80 group-hover:opacity-100 transition">
                  <ServerOff className="w-5 h-5 text-red-500 mt-1" />
                  <div>
                    <h4 className="font-bold text-lg text-slate-200 mb-1">內地剪接 App</h4>
                    <p className="text-slate-400 text-sm">要上傳內地伺服器過審，隨時被下架。</p>
                  </div>
                </li>
                <li className="flex gap-4 items-start opacity-80 group-hover:opacity-100 transition">
                  <Clock className="w-5 h-5 text-red-500 mt-1" />
                  <div>
                    <h4 className="font-bold text-lg text-slate-200 mb-1">人手打字幕 (最痛苦)</h4>
                    <p className="text-slate-400 text-sm">10 分鐘片 = 3 小時工作，OT 到 11 點。</p>
                  </div>
                </li>
              </ul>
            </div>

            {/* Us Card */}
            <div className="group bg-gradient-to-b from-slate-800 to-slate-900 p-8 rounded-3xl border-2 border-primary/50 hover:border-primary transition-all duration-300 shadow-[0_0_50px_rgba(255,84,0,0.1)] hover:shadow-[0_0_50px_rgba(255,84,0,0.2)] relative overflow-hidden transform md:-translate-y-4 z-10">
              <div className="absolute inset-0 bg-gradient-to-tr from-white/0 via-white/5 to-white/0 opacity-0 group-hover:opacity-100 transition duration-700 pointer-events-none transform translate-x-full group-hover:translate-x-0" />
              <div className="absolute -top-1 -right-1">
                <span className="bg-primary text-white text-xs font-bold px-3 py-1 rounded-bl-xl rounded-tr-lg shadow-lg">
                  RECOMMENDED
                </span>
              </div>

              <div className="flex justify-between items-center mb-8">
                <span className="bg-primary/10 text-primary px-4 py-1.5 rounded-full font-bold text-sm border border-primary/20 flex items-center gap-2">
                  <Sparkles className="w-3 h-3" /> Canto-Beats
                </span>
                <Smile className="w-8 h-8 text-primary" />
              </div>

              {/* Progress Bar */}
              <div className="mb-8 bg-slate-800/80 p-4 rounded-xl border border-primary/20 shadow-inner">
                <div className="flex justify-between text-xs text-primary mb-2 font-mono font-bold">
                  <span>識別準確率</span>
                  <span>99.9%</span>
                </div>
                <div className="w-full bg-slate-700/50 h-3 rounded-full overflow-hidden">
                  <div className="bg-gradient-to-r from-orange-500 to-yellow-400 h-full rounded-full w-[99.9%] shadow-[0_0_15px_rgba(255,165,0,0.5)]" />
                </div>
                <p className="text-xs text-primary/70 mt-2 text-right">
                  連懶音、中英夾雜都完美識別
                </p>
              </div>

              <ul className="space-y-6 relative z-10">
                <li className="flex gap-4 items-start">
                  <Check className="w-5 h-5 text-primary mt-1" />
                  <div>
                    <h4 className="font-bold text-lg text-white mb-1">香港人專屬引擎</h4>
                    <p className="text-slate-300 text-sm">連『食飯未』『hea 咗未』都 100% 準確。</p>
                  </div>
                </li>
                <li className="flex gap-4 items-start">
                  <ShieldCheck className="w-5 h-5 text-primary mt-1" />
                  <div>
                    <h4 className="font-bold text-lg text-white mb-1">本地運算，0 審查</h4>
                    <p className="text-slate-300 text-sm">完全離線運行 (Offline)，絕對私隱。</p>
                  </div>
                </li>
                <li className="flex gap-4 items-start">
                  <Coins className="w-5 h-5 text-primary mt-1" />
                  <div>
                    <h4 className="font-bold text-lg text-white mb-1">HK$599 買斷</h4>
                    <p className="text-slate-300 text-sm">Descript 收 US$12/月，我哋一次過收費。</p>
                  </div>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
