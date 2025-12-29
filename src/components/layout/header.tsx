"use client";

import * as React from "react";
import Link from "next/link";
import { Menu, X } from "lucide-react";
import Image from "next/image";

import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";

const navLinks = [
  { href: "#features", label: "功能特色" },
  { href: "#comparison", label: "優勢對比" },
  { href: "#pricing", label: "定價" },
  { href: "/contact", label: "聯絡我們" },
];

export default function Header() {
  const [isMenuOpen, setIsMenuOpen] = React.useState(false);

  return (
    <nav className="sticky top-0 z-50 w-full bg-[#0F172A]/80 backdrop-blur-md border-b border-white/5 transition-all duration-300">
      <div className="container mx-auto px-6 py-4 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <Image src="/app icon_002.png" alt="Canto-Beats" width={32} height={32} />
          <span className="text-xl font-bold tracking-tight">
            Canto-Beats
          </span>
        </div>

        {/* Desktop Navigation */}
        <div className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-300">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="hover:text-primary transition-colors"
            >
              {link.label}
            </Link>
          ))}
        </div>

        {/* CTA Button */}
        <Link
          href="#pricing"
          className="hidden md:block bg-primary/10 text-primary hover:bg-primary hover:text-white px-5 py-2 rounded-lg font-bold text-sm transition border border-primary/20"
        >
          立即購買
        </Link>

        {/* Mobile Menu */}
        <Sheet open={isMenuOpen} onOpenChange={setIsMenuOpen}>
          <SheetTrigger asChild>
            <Button
              variant="ghost"
              className="px-2 text-base hover:bg-transparent focus-visible:bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0 md:hidden"
            >
              <Menu className="h-6 w-6" />
              <span className="sr-only">Toggle Menu</span>
            </Button>
          </SheetTrigger>
          <SheetContent side="right" className="w-[300px] sm:w-[400px] bg-slate-900 border-slate-700">
            <div className="flex items-center justify-between">
              <Link href="/" className="flex items-center gap-2" onClick={() => setIsMenuOpen(false)}>
                <Image src="/app icon_002.png" alt="Canto-Beats" width={24} height={24} />
                <span className="font-bold">Canto-Beats</span>
              </Link>
              <Button variant="ghost" size="icon" onClick={() => setIsMenuOpen(false)}>
                <X className="h-6 w-6" />
              </Button>
            </div>
            <div className="mt-6 flex flex-col space-y-4">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="rounded-md p-2 font-medium text-slate-300 hover:text-primary hover:bg-slate-800 transition"
                  onClick={() => setIsMenuOpen(false)}
                >
                  {link.label}
                </Link>
              ))}
              <Link
                href="#pricing"
                className="mt-4 bg-primary text-white px-4 py-3 rounded-lg font-bold text-center transition hover:bg-primary/90"
                onClick={() => setIsMenuOpen(false)}
              >
                立即購買
              </Link>
            </div>
          </SheetContent>
        </Sheet>
      </div>
    </nav>
  );
}
