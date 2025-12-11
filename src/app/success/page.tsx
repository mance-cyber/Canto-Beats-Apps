"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { Loader2, CheckCircle, AlertTriangle, Copy, ArrowLeft } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { getLicenseKey } from "@/app/actions";
import { useToast } from "@/hooks/use-toast";
import Header from "@/components/layout/header";
import Footer from "@/components/layout/footer";

function SuccessContent() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("session_id");
  const [licenseKey, setLicenseKey] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    if (!sessionId) {
      setError("無效嘅 Session ID，請重新嘗試。");
      setIsLoading(false);
      return;
    }

    const fetchLicenseKey = async () => {
      try {
        const key = await getLicenseKey(sessionId);
        setLicenseKey(key);
      } catch (e: any) {
        setError(e.message || "發生未知錯誤，請聯絡我哋。");
      } finally {
        setIsLoading(false);
      }
    };

    fetchLicenseKey();
  }, [sessionId]);

  const handleCopy = () => {
    if (licenseKey) {
      navigator.clipboard.writeText(licenseKey);
      toast({
        title: "搞掂！",
        description: "License Key 已經複製咗。",
      });
    }
  };

  return (
    <div className="container flex flex-1 items-center justify-center py-12 md:py-24">
      <Card className="w-full max-w-lg text-center shadow-2xl">
        <CardHeader>
          {isLoading ? (
            <Loader2 className="mx-auto h-12 w-12 animate-spin text-primary" />
          ) : error ? (
            <AlertTriangle className="mx-auto h-12 w-12 text-destructive" />
          ) : (
            <CheckCircle className="mx-auto h-12 w-12 text-green-500" />
          )}
          <CardTitle className="mt-4 text-2xl font-bold">
            {isLoading
              ? "處理緊你嘅訂單..."
              : error
              ? "呀！出咗少少問題"
              : "多謝支持！交易成功！"}
          </CardTitle>
          <CardDescription>
            {isLoading
              ? "我哋努力緊，幫你生成緊個 License Key..."
              : error
              ? error
              : "你嘅 License Key 已經準備好，記住 save 低佢！"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {licenseKey && (
            <div className="flex flex-col items-center gap-4 rounded-lg border bg-muted p-4">
              <p className="font-mono text-xl font-bold tracking-widest text-primary md:text-2xl">
                {licenseKey}
              </p>
              <Button onClick={handleCopy} className="w-full">
                <Copy className="mr-2 h-4 w-4" />
                複製 License Key
              </Button>
            </div>
          )}
           <div className="mt-6 flex flex-col items-center gap-2">
            <p className="text-sm text-muted-foreground">
                {licenseKey ? "我哋亦都將個 Key send 咗去你嘅電郵。" : "如果遇到問題，可以隨時搵我哋。"}
            </p>
             <Button variant="ghost" asChild>
                <Link href="/">
                    <ArrowLeft className="mr-2 h-4 w-4" />
                    返回主頁
                </Link>
             </Button>
           </div>
        </CardContent>
      </Card>
    </div>
  );
}


export default function SuccessPage() {
    return (
        <div className="flex min-h-dvh flex-col">
            <Header />
            <main className="flex flex-1">
                <Suspense fallback={<div className="flex-1 flex items-center justify-center"><Loader2 className="h-12 w-12 animate-spin text-primary" /></div>}>
                    <SuccessContent />
                </Suspense>
            </main>
            <Footer />
        </div>
    )
}
