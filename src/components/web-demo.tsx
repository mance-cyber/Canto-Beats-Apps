"use client";

import { useState, useRef, useEffect } from "react";
import { Upload, Mic, Loader2, Square, Wand2 } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";

export function WebDemo() {
  const [activeTab, setActiveTab] = useState("upload");
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [fileName, setFileName] = useState("");

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const mockTranscript =
    "喂，老細，今日晏晝食乜嘢啊？不如我哋去茶餐廳啦，我想食個沙嗲牛麵，跟杯凍檸茶少甜，唔該。";

  const processTranscription = () => {
    setIsLoading(true);
    setTranscript("");
    setTimeout(() => {
      setTranscript(mockTranscript);
      setIsLoading(false);
    }, 2000);
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      const file = event.target.files[0];
      // Limit file size to 50MB for demo
      if (file.size > 50 * 1024 * 1024) {
        alert("檔案太大啦，試下細過 50MB 嘅檔案。");
        return;
      }
      setFileName(file.name);
      processTranscription();
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };
      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/wav" });
        audioChunksRef.current = [];
        // In a real app, you would send this blob to the server
        processTranscription();
        // Clean up the stream
        stream.getTracks().forEach(track => track.stop());
      };
      audioChunksRef.current = [];
      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Error accessing microphone:", err);
      alert("開唔到咪高峰喎，請檢查你嘅設定。");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  useEffect(() => {
    // Cleanup function to stop recording and stream if component unmounts
    return () => {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
        mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  return (
    <Card className="w-full shadow-2xl">
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <CardHeader>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="upload">
                <Upload className="mr-2 h-4 w-4" />
                上載檔案
              </TabsTrigger>
              <TabsTrigger value="record">
                <Mic className="mr-2 h-4 w-4" />
                即時錄音
              </TabsTrigger>
            </TabsList>
        </CardHeader>
        <CardContent>
          <TabsContent value="upload" className="mt-0">
            <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-border p-8 text-center">
              <Upload className="mb-4 h-12 w-12 text-muted-foreground" />
              <h3 className="text-lg font-semibold">上載音頻或影片</h3>
              <p className="mb-4 text-sm text-muted-foreground">
                支援 MP3, WAV, MP4 等格式 (Demo 最長 60 秒)
              </p>
              <Button asChild>
                <label htmlFor="file-upload" className="cursor-pointer">
                  選擇檔案
                </label>
              </Button>
              <input
                id="file-upload"
                type="file"
                className="hidden"
                accept="audio/*,video/*"
                onChange={handleFileChange}
              />
              {fileName && (
                <p className="mt-4 text-sm text-muted-foreground">
                  已選擇: {fileName}
                </p>
              )}
            </div>
          </TabsContent>
          <TabsContent value="record" className="mt-0">
            <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-border p-8 text-center">
              <Mic
                className={cn(
                  "mb-4 h-12 w-12 text-muted-foreground",
                  isRecording && "text-destructive animate-pulse"
                )}
              />
              <h3 className="text-lg font-semibold">
                {isRecording ? "錄音中..." : "即時錄音"}
              </h3>
              <p className="mb-4 text-sm text-muted-foreground">
                {isRecording
                  ? "Demo 最長可以錄 60 秒"
                  : "撳下面個掣開始錄音"}
              </p>
              {!isRecording ? (
                <Button onClick={startRecording}>
                  <Mic className="mr-2 h-4 w-4" />
                  開始錄音
                </Button>
              ) : (
                <Button onClick={stopRecording} variant="destructive">
                  <Square className="mr-2 h-4 w-4" />
                  停止錄音
                </Button>
              )}
            </div>
          </TabsContent>

          {(isLoading || transcript) && (
            <div className="mt-6">
              <h3 className="mb-2 flex items-center text-lg font-semibold">
                <Wand2 className="mr-2 h-5 w-5 text-primary" />
                轉錄結果
              </h3>
              <div className="relative">
                <Textarea
                  readOnly
                  value={transcript}
                  placeholder="轉錄緊，俾少少時間..."
                  className="min-h-[120px] text-base"
                />
                {isLoading && (
                  <div className="absolute inset-0 flex items-center justify-center rounded-md bg-background/80">
                    <Loader2 className="h-8 w-8 animate-spin text-primary" />
                  </div>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Tabs>
    </Card>
  );
}
