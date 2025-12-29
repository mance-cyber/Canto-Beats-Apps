import { Check } from "lucide-react";
import Link from "next/link";

const features = [
  "無限生成時長",
  "匯出 SRT / ASS / TXT",
  "優先技術支援",
];

const STRIPE_PAYMENT_LINK = "https://buy.stripe.com/7sY00b9A5gFSaVE84I4Vy00";

export default function PricingSection() {

  return (
    <section id="pricing" className="py-24 container mx-auto px-6">
      <div className="max-w-lg mx-auto bg-gradient-to-b from-slate-800 to-slate-900 rounded-3xl p-1 border border-slate-700 relative hover:border-primary/30 transition duration-300">
        {/* Limited Offer Badge */}
        <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-gradient-to-r from-red-500 to-orange-500 text-white px-4 py-1 rounded-full text-sm font-bold shadow-lg whitespace-nowrap z-20">
          免費 3 個月更新 🔥
        </div>

        <div className="bg-card rounded-[22px] p-8 md:p-12 text-center h-full flex flex-col relative overflow-hidden">
          {/* Subtle Gradient bg */}
          <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-50 pointer-events-none" />

          <h3 className="text-2xl font-bold text-slate-300 mb-2 relative z-10">
            永久買斷版
          </h3>

          <div className="flex items-baseline justify-center gap-1 my-6 relative z-10">
            <span className="text-xl text-slate-500">HK$</span>
            <span className="text-6xl font-black text-white tracking-tight">599</span>
          </div>

          <ul className="text-left space-y-4 mb-6 flex-1 pl-4 relative z-10">
            {features.map((feature, index) => (
              <li key={index} className="flex items-center gap-3 text-slate-300">
                <Check className="text-green-400 w-5 h-5 flex-shrink-0" />
                <span>{feature}</span>
              </li>
            ))}
          </ul>

          <div className="mb-6 p-4 bg-primary/10 border border-primary/20 rounded-lg relative z-10">
            <p className="text-sm text-primary font-medium">
              ✅ 付款成功後，授權序號將立即發送至你的電郵
            </p>
          </div>

          <Link
            href={STRIPE_PAYMENT_LINK}
            target="_blank"
            className="w-full bg-primary hover:bg-primary-hover text-white py-4 rounded-xl font-bold text-xl shadow-lg shadow-primary/25 transition transform hover:-translate-y-1 relative z-10 block text-center"
          >
            立即購買
          </Link>

          <p className="mt-4 text-xs text-slate-500 relative z-10">
            支援 Visa / Master / AlipayHK / WeChat Pay
          </p>
        </div>
      </div>
    </section>
  );
}
