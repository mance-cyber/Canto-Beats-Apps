"use client";

import { ChevronDown } from "lucide-react";

const faqs = [
  {
    question: "真係可以永久使用？",
    answer:
      "係！只要俾一次 HK$599，你就可以永久使用目前版本，並且免費獲得未來所有 2.x 版本嘅更新。冇任何隱藏月費。",
  },
  {
    question: "識別準確率有幾高？",
    answer:
      "針對香港人嘅說話習慣訓練，對於中英夾雜（例如「食個 Lunch 先」）、懶音（例如「恆生銀行」）都有極高識別率。你可以用上面嘅 Demo 試下先！",
  },
  {
    question: "電腦配置要求高唔高？",
    answer:
      "唔算高。只要係近 5 年內買嘅電腦都跑得郁。如果你用 Mac M1/M2/M3 系列，速度會非常之快。",
  },
];

export default function FaqSection() {
  return (
    <section className="py-16 bg-slate-900/50">
      <div className="container mx-auto px-6 max-w-3xl">
        <h2 className="text-2xl font-bold mb-8 text-center">常見問題</h2>

        <div className="space-y-4">
          {faqs.map((faq, index) => (
            <details
              key={index}
              className="group bg-card p-4 rounded-lg cursor-pointer border border-transparent hover:border-slate-700 open:border-primary/50 transition-all duration-300"
            >
              <summary className="flex justify-between items-center font-medium list-none">
                <span>{faq.question}</span>
                <span className="transition group-open:rotate-180">
                  <ChevronDown className="w-5 h-5" />
                </span>
              </summary>
              <p className="text-slate-400 mt-3 text-sm leading-relaxed">
                {faq.answer}
              </p>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
}
