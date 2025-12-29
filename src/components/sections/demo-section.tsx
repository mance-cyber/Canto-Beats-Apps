"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Youtube,
  GraduationCap,
  MessageCircle,
  PlayCircle,
  Mic,
  Copy,
  RefreshCcw,
  ArrowRight,
  BookOpen,
  Languages,
  Hash,
} from "lucide-react";

const scenarios = [
  {
    icon: Youtube,
    iconColor: "bg-red-500/10 text-red-500",
    title: "YouTuber Vlog",
    description: "測試：語速快、生活用語",
    text: "Hello 大家好，又係我！今日帶大家嚟到尖沙咀呢間新開嘅 Cafe 試食。聽講佢哋個 All Day Breakfast 好出名，排隊都排咗成個鐘。即刻試下係咪真係咁好食，定係得個樣先！",
    meta: "需時: 0.8秒 | 準確率: 99.8%",
  },
  {
    icon: GraduationCap,
    iconColor: "bg-blue-500/10 text-blue-500",
    title: "網上課程教學",
    description: "測試：學術概念、清晰講解",
    text: "好，咁我哋依家進入第 3 課，講下點樣用 Python 嘅 for loop。首先，大家打開你哋嘅 IDE，跟住我輸入 for i in range 括號 10，然後 colon。記住呢度個 indentation 好重要，一定要用 4 個 space。如果唔係，個 program 就會出 error 㗎喇。",
    meta: "需時: 0.7秒 | 準確率: 99.9%",
  },
  {
    icon: MessageCircle,
    iconColor: "bg-green-500/10 text-green-500",
    title: "日常懶音對話",
    description: "測試：嚴重懶音、口語助詞",
    text: "而家天氣咁鬼熱，真係唔想出街食飯囉。不如叫外賣算啦，你哋想食譚仔定係麥當勞呀？其實我無所謂架，最緊要係有凍飲，熱死辣辣真係搞唔掂。",
    meta: "需時: 0.5秒 | 準確率: 99.7%",
  },
];

// 口語轉書面語對照表
const colloquialToFormal: Record<string, string> = {
  "係": "是",
  "唔": "不",
  "咁": "這麼",
  "嘅": "的",
  "啲": "些",
  "嚟": "來",
  "喺": "在",
  "俾": "給",
  "佢": "他",
  "佢哋": "他們",
  "你哋": "你們",
  "我哋": "我們",
  "咗": "了",
  "緊": "著",
  "住": "著",
  "啦": "了",
  "囉": "了",
  "呀": "",
  "架": "",
  "嘛": "",
  "咩": "什麼",
  "點": "怎麼",
  "點樣": "怎樣",
  "點解": "為什麼",
  "幾時": "什麼時候",
  "邊度": "哪裡",
  "邊個": "誰",
  "乜": "什麼",
  "乜嘢": "什麼",
  "冇": "沒有",
  "而家": "現在",
  "琴日": "昨天",
  "聽日": "明天",
  "尋日": "昨天",
  "今日": "今天",
  "出街": "外出",
  "返屋企": "回家",
  "屋企": "家裡",
  "食飯": "吃飯",
  "飲嘢": "喝東西",
  "瞓覺": "睡覺",
  "搵": "找",
  "攞": "拿",
  "睇": "看",
  "傾": "聊",
  "傾偈": "聊天",
  "嬲": "生氣",
  "驚": "怕",
  "好似": "好像",
  "可能": "可能",
  "其實": "其實",
  "不如": "不如",
  "算啦": "算了",
  "搞掂": "搞定",
  "得": "可以",
  "唔得": "不行",
  "好耐": "很久",
  "好多": "很多",
  "少少": "一點",
  "成日": "經常",
  "次次": "每次",
  "個個": "每個人",
  "啱啱": "剛剛",
  "真係": "真的",
  "咁鬼": "這麼",
  "最緊要": "最重要",
  "無所謂": "無所謂",
  "排隊": "排隊",
  "排咗": "排了",
  "成個鐘": "整整一小時",
  "即刻": "立刻",
  "定係": "還是",
  "講下": "說一下",
  "簡單嚟講": "簡單來說",
  "譬如": "例如",
  "學識": "學會",
  "身邊": "身邊",
  "聽講": "聽說",
  "外賣": "外賣",
  "凍飲": "冷飲",
  "熱死": "熱死",
};

// 英文翻譯對照表
const englishTranslations: Record<string, string> = {
  "Hello": "你好",
  "Cafe": "咖啡店",
  "All Day Breakfast": "全日早餐",
  "WhatsApp": "通訊軟件",
  "YouTuber": "YouTube創作者",
  "Vlog": "視頻日誌",
  "AI": "人工智能",
  "SRT": "字幕檔案格式",
  "Python": "編程語言",
  "for loop": "迴圈",
  "IDE": "程式編輯器",
  "range": "範圍函數",
  "colon": "冒號",
  "indentation": "縮排",
  "space": "空格",
  "program": "程式",
  "error": "錯誤",
};

// 數字轉換
const arabicToChineseNum: Record<string, string> = {
  "0": "零", "1": "一", "2": "二", "3": "三", "4": "四",
  "5": "五", "6": "六", "7": "七", "8": "八", "9": "九",
  "10": "十", "100": "百", "1000": "千",
};

const arabicToRoman: Record<number, string> = {
  1: "I", 2: "II", 3: "III", 4: "IV", 5: "V",
  6: "VI", 7: "VII", 8: "VIII", 9: "IX", 10: "X",
  50: "L", 100: "C", 500: "D", 1000: "M",
};

function toRomanNumeral(num: number): string {
  if (num <= 0 || num > 3999) return num.toString();
  const romanNumerals: [number, string][] = [
    [1000, "M"], [900, "CM"], [500, "D"], [400, "CD"],
    [100, "C"], [90, "XC"], [50, "L"], [40, "XL"],
    [10, "X"], [9, "IX"], [5, "V"], [4, "IV"], [1, "I"]
  ];
  let result = "";
  for (const [value, symbol] of romanNumerals) {
    while (num >= value) {
      result += symbol;
      num -= value;
    }
  }
  return result;
}

function toChineseNumeral(num: number): string {
  if (num === 0) return "零";
  const digits = ["", "一", "二", "三", "四", "五", "六", "七", "八", "九"];
  const units = ["", "十", "百", "千", "萬"];
  let result = "";
  let unitIndex = 0;
  while (num > 0) {
    const digit = num % 10;
    if (digit !== 0) {
      result = digits[digit] + units[unitIndex] + result;
    } else if (result && !result.startsWith("零")) {
      result = "零" + result;
    }
    num = Math.floor(num / 10);
    unitIndex++;
  }
  return result.replace(/^一十/, "十");
}

// 轉換函數
function convertToFormal(text: string): string {
  let result = text;
  // 按長度排序，先替換較長的詞組
  const sortedKeys = Object.keys(colloquialToFormal).sort((a, b) => b.length - a.length);
  for (const key of sortedKeys) {
    result = result.split(key).join(colloquialToFormal[key]);
  }
  return result;
}

function translateEnglish(text: string): string {
  let result = text;
  for (const [eng, chi] of Object.entries(englishTranslations)) {
    const regex = new RegExp(eng, "gi");
    result = result.replace(regex, `${eng}（${chi}）`);
  }
  return result;
}

function convertNumbers(text: string, format: "chinese" | "roman"): string {
  return text.replace(/\d+/g, (match) => {
    const num = parseInt(match, 10);
    if (format === "roman") {
      return num <= 3999 ? toRomanNumeral(num) : match;
    }
    return toChineseNumeral(num);
  });
}

export default function DemoSection() {
  const [state, setState] = useState<"select" | "progress" | "result">("select");
  const [currentScenario, setCurrentScenario] = useState(0);
  const [progress, setProgress] = useState(0);
  const [progressText, setProgressText] = useState("初始化...");
  const [displayedText, setDisplayedText] = useState("");

  // 轉換選項
  const [formalMode, setFormalMode] = useState(false); // false=口語, true=書面語
  const [translateMode, setTranslateMode] = useState(false);
  const [numberFormat, setNumberFormat] = useState<"arabic" | "chinese">("arabic"); // 兩種切換

  const selectScenario = (id: number) => {
    setCurrentScenario(id);
    startProcessing();
  };

  const startProcessing = () => {
    setState("progress");
    setProgress(0);
    setProgressText("初始化...");

    let width = 0;
    const interval = setInterval(() => {
      width += Math.random() * 8;
      if (width > 80 && width < 90) width += 0.5;

      if (width >= 100) {
        width = 100;
        clearInterval(interval);
        setTimeout(() => showResult(), 400);
      }

      setProgress(Math.floor(width));

      if (width < 30) setProgressText("正在加載模擬音頻...");
      else if (width < 60) setProgressText("AI 正在去除背景雜音...");
      else if (width < 90) setProgressText("正在轉換粵語文字...");
      else setProgressText("即將完成...");
    }, 80);
  };

  const showResult = () => {
    setState("result");
    setDisplayedText("");

    const text = scenarios[currentScenario].text;
    let i = 0;
    const typeInterval = setInterval(() => {
      setDisplayedText(text.substring(0, i + 1));
      i++;
      if (i >= text.length) clearInterval(typeInterval);
    }, 25);
  };

  const resetDemo = () => {
    setState("select");
    setProgress(0);
    setDisplayedText("");
    setFormalMode(false);
    setTranslateMode(false);
    setNumberFormat("arabic");
  };

  // 數字格式切換
  const toggleNumberFormat = () => {
    setNumberFormat((prev) => prev === "arabic" ? "chinese" : "arabic");
  };

  // 獲取處理後的文字
  const getProcessedText = () => {
    let text = displayedText;
    if (formalMode) {
      text = convertToFormal(text);
    }
    if (translateMode) {
      text = translateEnglish(text);
    }
    if (numberFormat !== "arabic") {
      text = convertNumbers(text, numberFormat);
    }
    return text;
  };

  const copyResult = () => {
    navigator.clipboard.writeText(getProcessedText());
    alert("文字已複製！");
  };

  return (
    <section id="demo" className="bg-card/50 py-20 border-y border-white/5 relative overflow-hidden">
      <div className="container mx-auto px-6 relative z-10">
        <div className="max-w-4xl mx-auto bg-card border border-slate-700 rounded-2xl p-8 shadow-2xl relative overflow-hidden">
          {/* Decorative gradient blob */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-3xl -mr-32 -mt-32 pointer-events-none" />

          <div className="text-center mb-10">
            <h2 className="text-5xl md:text-6xl font-black mb-4 text-white drop-shadow-xl">
              即時試玩
            </h2>
            <p className="text-xl text-primary font-bold tracking-wider mb-2 uppercase">
              1 分鐘極速體驗
            </p>
            <p className="text-slate-400">
              請選擇一個場景，即時睇下 AI 點樣完美識別不同語氣嘅廣東話！
            </p>
          </div>

          {/* Scenario Selector */}
          {state === "select" && (
            <div className="grid md:grid-cols-3 gap-4 mb-8">
              {scenarios.map((scenario, index) => {
                const Icon = scenario.icon;
                return (
                  <button
                    key={index}
                    onClick={() => selectScenario(index)}
                    className="bg-slate-800 hover:bg-slate-700 border-2 border-slate-700 hover:border-primary p-6 rounded-xl transition text-left group relative overflow-hidden transform hover:-translate-y-1 hover:shadow-lg"
                  >
                    <div className={`w-12 h-12 ${scenario.iconColor} rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition`}>
                      <Icon className="w-6 h-6" />
                    </div>
                    <h3 className="font-bold text-lg mb-1 text-white">{scenario.title}</h3>
                    <p className="text-sm text-slate-400">{scenario.description}</p>
                    <div className="absolute bottom-4 right-4 opacity-0 group-hover:opacity-100 transition transform translate-y-2 group-hover:translate-y-0 text-primary">
                      <PlayCircle className="w-6 h-6" />
                    </div>
                  </button>
                );
              })}
            </div>
          )}

          {/* Progress Area */}
          {state === "progress" && (
            <div className="py-12 px-4 max-w-xl mx-auto text-center relative">
              <div className="w-16 h-16 bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-6 animate-bounce text-primary relative z-10">
                <Mic className="w-8 h-8" />
              </div>
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-32 h-32 bg-primary/20 rounded-full blur-xl animate-pulse -mt-8" />
              <h3 className="text-xl font-bold mb-6 relative z-10">正在模擬分析音頻...</h3>
              <div className="w-full bg-slate-700 rounded-full h-3 overflow-hidden mb-2 relative z-10">
                <div
                  className="bg-primary h-3 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <div className="flex justify-between text-xs text-slate-500 font-mono relative z-10">
                <span>{progressText}</span>
                <span>{progress}%</span>
              </div>
            </div>
          )}

          {/* Result Area */}
          {state === "result" && (
            <div className="mt-4 animate-fade-in-up">
              <div className="bg-slate-900 rounded-xl p-6 border border-slate-700 relative shadow-inner">
                <div className="absolute top-4 right-4 flex gap-2">
                  <button
                    onClick={copyResult}
                    className="text-xs bg-slate-800 hover:bg-slate-700 px-3 py-1.5 rounded-md text-slate-300 transition flex items-center gap-1"
                  >
                    <Copy className="w-3 h-3" /> 複製
                  </button>
                </div>

                <div className="flex items-center gap-3 mb-4 border-b border-slate-800 pb-4">
                  <span className="bg-green-500/10 text-green-500 text-xs font-bold px-2 py-1 rounded border border-green-500/20">
                    識別成功
                  </span>
                  <span className="text-slate-500 text-xs">{scenarios[currentScenario].meta}</span>
                </div>

                {/* 轉換工具列 */}
                <div className="flex flex-wrap gap-3 mb-4 pb-4 border-b border-slate-800">
                  <span className="text-xs text-slate-500 flex items-center">即時轉換：</span>

                  {/* 口語/書面語 切換 */}
                  <button
                    onClick={() => setFormalMode(!formalMode)}
                    className="text-xs px-3 py-1.5 rounded-full flex items-center gap-1.5 transition border bg-slate-800 border-slate-700 hover:border-purple-500/50 group"
                  >
                    <BookOpen className="w-3 h-3 text-purple-400" />
                    <span className={formalMode ? "text-slate-500" : "text-purple-400 font-medium"}>口語</span>
                    <span className="text-slate-600">/</span>
                    <span className={formalMode ? "text-purple-400 font-medium" : "text-slate-500"}>書面語</span>
                  </button>

                  {/* 英文翻譯 */}
                  <button
                    onClick={() => setTranslateMode(!translateMode)}
                    className={`text-xs px-3 py-1.5 rounded-full flex items-center gap-1.5 transition border ${
                      translateMode
                        ? "bg-blue-500/20 text-blue-400 border-blue-500/50"
                        : "bg-slate-800 text-slate-400 border-slate-700 hover:border-blue-500/50 hover:text-blue-400"
                    }`}
                  >
                    <Languages className="w-3 h-3" />
                    英文翻譯
                  </button>

                  {/* 數字格式 切換 */}
                  <button
                    onClick={toggleNumberFormat}
                    className="text-xs px-3 py-1.5 rounded-full flex items-center gap-1.5 transition border bg-slate-800 border-slate-700 hover:border-amber-500/50 group"
                  >
                    <Hash className="w-3 h-3 text-amber-400" />
                    <span className={numberFormat === "arabic" ? "text-amber-400 font-medium" : "text-slate-500"}>123</span>
                    <span className="text-slate-600">/</span>
                    <span className={numberFormat === "chinese" ? "text-amber-400 font-medium" : "text-slate-500"}>一二三</span>
                  </button>
                </div>

                <div className="pl-4 border-l-2 border-primary/50 py-1">
                  <p className="font-medium text-slate-200 leading-relaxed text-base md:text-lg">
                    {getProcessedText()}
                  </p>
                </div>

                <div className="mt-6 pt-4 border-t border-slate-800 flex flex-col md:flex-row justify-between items-center gap-4">
                  <p className="text-slate-500 text-xs">
                    注意：試玩版僅顯示純文字，完整版可匯出 SRT 字幕。
                  </p>
                  <Link
                    href="#pricing"
                    className="bg-primary/10 hover:bg-primary/20 text-primary px-4 py-2 rounded-lg text-sm font-bold transition flex items-center gap-2"
                  >
                    解鎖完整 SRT 功能 <ArrowRight className="w-4 h-4" />
                  </Link>
                </div>
              </div>

              <button
                onClick={resetDemo}
                className="mt-6 mx-auto flex items-center gap-2 text-slate-500 hover:text-white transition text-sm"
              >
                <RefreshCcw className="w-4 h-4" /> 試玩其他場景
              </button>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
