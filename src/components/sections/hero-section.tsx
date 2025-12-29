"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import { Download } from "lucide-react";

export default function HeroSection() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const headerRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let particles: Particle[] = [];
    const mouse = { x: null as number | null, y: null as number | null };

    function resize() {
      if (!canvas || !headerRef.current) return;
      canvas.width = headerRef.current.offsetWidth;
      canvas.height = headerRef.current.offsetHeight;
      initParticles();
    }

    class Particle {
      x: number;
      y: number;
      vx: number;
      vy: number;
      size: number;

      constructor() {
        this.x = Math.random() * (canvas?.width || 800);
        this.y = Math.random() * (canvas?.height || 600);
        this.vx = (Math.random() - 0.5) * 0.5;
        this.vy = (Math.random() - 0.5) * 0.5;
        this.size = Math.random() * 2 + 1;
      }

      update() {
        this.x += this.vx;
        this.y += this.vy;
        if (this.x < 0 || this.x > (canvas?.width || 800)) this.vx *= -1;
        if (this.y < 0 || this.y > (canvas?.height || 600)) this.vy *= -1;
      }

      draw() {
        if (!ctx) return;
        ctx.fillStyle = "rgba(255, 255, 255, 0.3)";
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    function initParticles() {
      particles = [];
      const particleCount = Math.floor(
        ((canvas?.width || 800) * (canvas?.height || 600)) / 15000
      );
      for (let i = 0; i < particleCount; i++) {
        particles.push(new Particle());
      }
    }

    function animate() {
      if (!ctx || !canvas) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      particles.forEach((p) => {
        p.update();
        p.draw();

        if (mouse.x != null && mouse.y != null) {
          const dx = p.x - mouse.x;
          const dy = p.y - mouse.y;
          const distance = Math.sqrt(dx * dx + dy * dy);
          if (distance < 150) {
            ctx.strokeStyle = `rgba(255, 84, 0, ${1 - distance / 150})`;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(mouse.x, mouse.y);
            ctx.stroke();
          }
        }

        particles.forEach((p2) => {
          const dx = p.x - p2.x;
          const dy = p.y - p2.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 100) {
            ctx.strokeStyle = `rgba(148, 163, 184, ${0.1 * (1 - dist / 100)})`;
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
          }
        });
      });

      requestAnimationFrame(animate);
    }

    const handleMouseMove = (e: MouseEvent) => {
      if (!headerRef.current) return;
      const rect = headerRef.current.getBoundingClientRect();
      mouse.x = e.clientX - rect.left;
      mouse.y = e.clientY - rect.top;
    };

    const handleMouseLeave = () => {
      mouse.x = null;
      mouse.y = null;
    };

    window.addEventListener("resize", resize);
    headerRef.current?.addEventListener("mousemove", handleMouseMove);
    headerRef.current?.addEventListener("mouseleave", handleMouseLeave);

    resize();
    animate();

    return () => {
      window.removeEventListener("resize", resize);
    };
  }, []);

  return (
    <header
      ref={headerRef}
      className="container mx-auto px-6 pt-10 pb-20 text-center relative z-10 overflow-hidden"
    >
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full pointer-events-none z-0 opacity-40"
      />

      {/* Headline */}
      <h1 className="text-4xl md:text-6xl font-black mb-6 leading-tight relative z-10">
        全港最強
        <br />
        <span className="gradient-text">粵語自動字幕生成器</span>
      </h1>

      {/* Description */}
      <p className="text-slate-400 text-lg md:text-xl max-w-2xl mx-auto mb-8 leading-relaxed relative z-10">
        <span className="whitespace-nowrap">專為香港 YouTuber、Podcast 主設計。連<span className="text-white font-bold">潮語、懶音、中英夾雜</span>都完美識別。</span>
        <br />
        唔洗再逐隻字打，1 分鐘影片只需 1X 秒搞掂。
      </p>

      {/* Feature highlights */}
      <div className="flex flex-wrap justify-center gap-3 mb-10 relative z-10">
        <span className="bg-slate-800/60 border border-slate-700 px-4 py-2 rounded-full text-sm text-slate-300">
          ✍️ 廣東話<span className="font-bold text-primary text-base">秒轉</span>書面語
        </span>
        <span className="bg-slate-800/60 border border-slate-700 px-4 py-2 rounded-full text-sm text-slate-300">
          🌐 英文翻譯
        </span>
        <span className="bg-slate-800/60 border border-slate-700 px-4 py-2 rounded-full text-sm text-slate-300">
          🔢 數字文字轉換
        </span>
      </div>

      {/* CTA */}
      <div className="flex flex-col items-center justify-center gap-3 relative z-5">
        <Link
          href="#download"
          className="bg-primary hover:bg-primary-hover text-white pl-8 pr-12 py-5 rounded-xl font-bold text-xl transition transform hover:-translate-y-1 glow inline-flex items-center justify-center gap-1 shadow-lg shadow-primary/25"
        >
          <Download className="w-12 h-12" />
          <span className="flex flex-col items-start">
            <span>免費下載軟件</span>
            <span>（免費任玩）</span>
          </span>
        </Link>
        <p className="text-slate-400 text-sm">匯出功能需購買授權</p>
      </div>
    </header>
  );
}
