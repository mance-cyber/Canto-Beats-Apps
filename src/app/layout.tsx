import type { Metadata } from 'next';
import './globals.css';
import { Toaster } from "@/components/ui/toaster"
import Script from 'next/script';

export const metadata: Metadata = {
  title: '粵語自動字幕生成器｜99.9% 準確｜HK$599 買斷永久用',
  description: '全港最強粵語字幕工具，連粗口懶音都識別，3 秒即時試玩，HK$599 一次過永久解鎖 SRT/ASS 輸出！',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-HK">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+HK:wght@400;500;700;900&display=swap" rel="stylesheet" />
        
        {/* Placeholder for Google Analytics 4 */}
        {/* 
        <Script async src="https://www.googletagmanager.com/gtag/js?id=YOUR_GA4_ID"></Script>
        <Script id="ga-script">
          {`
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', 'YOUR_GA4_ID');
          `}
        </Script>
        */}

        {/* Placeholder for Meta Pixel */}
        {/*
        <Script id="meta-pixel-script">
          {`
            !function(f,b,e,v,n,t,s)
            {if(f.fbq)return;n=f.fbq=function(){n.callMethod?
            n.callMethod.apply(n,arguments):n.queue.push(arguments)};
            if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
            n.queue=[];t=b.createElement(e);t.async=!0;
            t.src=v;s=b.getElementsByTagName(e)[0];
            s.parentNode.insertBefore(t,s)}(window, document,'script',
            'https://connect.facebook.net/en_US/fbevents.js');
            fbq('init', 'YOUR_PIXEL_ID');
            fbq('track', 'PageView');
          `}
        </Script>
        <noscript>
          <img height="1" width="1" style={{display:'none'}}
               src="https://www.facebook.com/tr?id=YOUR_PIXEL_ID&ev=PageView&noscript=1"
          />
        </noscript>
        */}
      </head>
      <body className="font-sans antialiased selection:bg-primary selection:text-white overflow-x-hidden">
        {children}
        <Toaster />
      </body>
    </html>
  );
}
