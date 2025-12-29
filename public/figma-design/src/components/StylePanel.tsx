import { ChevronDown, Sparkles } from 'lucide-react';
import { useState } from 'react';

export function StylePanel() {
  const [languageOpen, setLanguageOpen] = useState(true);
  const [textProcessingOpen, setTextProcessingOpen] = useState(true);
  const [numberFormatOpen, setNumberFormatOpen] = useState(true);

  return (
    <div className="space-y-4">
      {/* AI Button */}
      <button className="w-full bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white py-4 rounded-xl transition-all border-2 border-cyan-400 shadow-lg shadow-cyan-500/50">
        <div className="flex items-center justify-center gap-2">
          <Sparkles className="w-5 h-5" />
          <span>開始 AI 轉寫</span>
        </div>
      </button>

      {/* Language Configuration */}
      <div className="bg-slate-800/50 rounded-xl border border-slate-700 overflow-hidden">
        <button
          onClick={() => setLanguageOpen(!languageOpen)}
          className="w-full px-4 py-3 flex items-center justify-between hover:bg-slate-700/30 transition-colors"
        >
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            <span>語言配置</span>
          </div>
          <ChevronDown className={`w-4 h-4 transition-transform ${languageOpen ? 'rotate-180' : ''}`} />
        </button>
        
        {languageOpen && (
          <div className="px-4 pb-4 space-y-3">
            {/* Row 1 */}
            <div className="flex items-center gap-2">
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="radio" name="language" className="sr-only peer" defaultChecked />
                <div className="w-5 h-5 bg-slate-600 peer-focus:outline-none rounded-full peer peer-checked:bg-cyan-500 peer-checked:border-4 peer-checked:border-white transition-all"></div>
              </label>
              <span className="text-sm">口語</span>
            </div>

            {/* Row 2 */}
            <div className="flex items-center gap-2">
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="radio" name="language" className="sr-only peer" />
                <div className="w-5 h-5 bg-slate-600 peer-focus:outline-none rounded-full peer peer-checked:bg-cyan-500 peer-checked:border-4 peer-checked:border-white transition-all"></div>
              </label>
              <span className="text-sm">半書面</span>
            </div>

            {/* Row 3 */}
            <div className="flex items-center gap-2">
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="radio" name="language" className="sr-only peer" />
                <div className="w-5 h-5 bg-slate-600 peer-focus:outline-none rounded-full peer peer-checked:bg-cyan-500 peer-checked:border-4 peer-checked:border-white transition-all"></div>
              </label>
              <span className="text-sm">條書面</span>
            </div>
          </div>
        )}
      </div>

      {/* Text Processing */}
      <div className="bg-slate-800/50 rounded-xl border border-slate-700 overflow-hidden">
        <button
          onClick={() => setTextProcessingOpen(!textProcessingOpen)}
          className="w-full px-4 py-3 flex items-center justify-between hover:bg-slate-700/30 transition-colors"
        >
          <div className="flex items-center gap-2">
            <span className="text-cyan-400">◉</span>
            <span>英文處理</span>
          </div>
          <ChevronDown className={`w-4 h-4 transition-transform ${textProcessingOpen ? 'rotate-180' : ''}`} />
        </button>
        
        {textProcessingOpen && (
          <div className="px-4 pb-4">
            <div className="flex gap-2">
              <button className="flex-1 bg-cyan-500 hover:bg-cyan-600 text-white py-2 px-4 rounded-lg transition-colors text-sm">
                常體
              </button>
              <button className="flex-1 bg-slate-700 hover:bg-slate-600 text-white py-2 px-4 rounded-lg transition-colors text-sm">
                翻譯
              </button>
              <button className="flex-1 bg-slate-700 hover:bg-slate-600 text-white py-2 px-4 rounded-lg transition-colors text-sm">
                顯示幣
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Number Format */}
      <div className="bg-slate-800/50 rounded-xl border border-slate-700 overflow-hidden">
        <button
          onClick={() => setNumberFormatOpen(!numberFormatOpen)}
          className="w-full px-4 py-3 flex items-center justify-between hover:bg-slate-700/30 transition-colors"
        >
          <div className="flex items-center gap-2">
            <span className="text-cyan-400">◉</span>
            <span>數字格式</span>
          </div>
          <ChevronDown className={`w-4 h-4 transition-transform ${numberFormatOpen ? 'rotate-180' : ''}`} />
        </button>
        
        {numberFormatOpen && (
          <div className="px-4 pb-4 space-y-3">
            {/* Position */}
            <div className="flex items-center gap-2">
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="radio" name="numberFormat" className="sr-only peer" defaultChecked />
                <div className="w-5 h-5 bg-slate-600 peer-focus:outline-none rounded-full peer peer-checked:bg-cyan-500 peer-checked:border-4 peer-checked:border-white transition-all"></div>
              </label>
              <span className="text-sm">同位置數字 (123)</span>
            </div>

            {/* Style */}
            <div className="flex items-center gap-2">
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="radio" name="numberFormat" className="sr-only peer" />
                <div className="w-5 h-5 bg-slate-600 peer-focus:outline-none rounded-full peer peer-checked:bg-cyan-500 peer-checked:border-4 peer-checked:border-white transition-all"></div>
              </label>
              <span className="text-sm">中文小寫(一二三)</span>
            </div>
          </div>
        )}
      </div>

      {/* Output Preview */}
      <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-4">
        <div className="text-sm text-slate-400 mb-2">輸出日誌</div>
        <div className="h-64 bg-slate-900/50 rounded-lg p-4 relative overflow-hidden">
          <div className="absolute bottom-4 right-4">
            <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-slate-900" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}