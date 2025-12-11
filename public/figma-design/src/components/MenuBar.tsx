import { ChevronRight } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';

export function MenuBar() {
  const [activeMenu, setActiveMenu] = useState<string | null>(null);
  const [showExportSubmenu, setShowExportSubmenu] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setActiveMenu(null);
        setShowExportSubmenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleMenu = (menu: string) => {
    setActiveMenu(activeMenu === menu ? null : menu);
    setShowExportSubmenu(false);
  };

  return (
    <div ref={menuRef} className="flex items-center gap-4 relative">
      {/* 檔案 Menu */}
      <div className="relative">
        <button
          onClick={() => toggleMenu('file')}
          className="px-3 py-1.5 hover:bg-slate-700/50 rounded transition-colors text-sm"
        >
          檔案<span className="text-slate-500">(F)</span>
        </button>

        {activeMenu === 'file' && (
          <div className="absolute top-full left-0 mt-1 w-56 bg-slate-800 border border-slate-600 rounded-lg shadow-xl z-50 overflow-hidden">
            <button className="w-full px-4 py-2.5 hover:bg-slate-700 transition-colors flex items-center justify-between text-left">
              <div className="flex items-center gap-3">
                <span className="text-sm">開啟影片</span>
                <span className="text-slate-500 text-sm">(O)...</span>
              </div>
              <span className="text-xs text-slate-400">Ctrl+O</span>
            </button>

            <div 
              className="relative"
              onMouseEnter={() => setShowExportSubmenu(true)}
              onMouseLeave={() => setShowExportSubmenu(false)}
            >
              <button className="w-full px-4 py-2.5 hover:bg-slate-700 transition-colors flex items-center justify-between text-left">
                <div className="flex items-center gap-3">
                  <span className="text-sm">導出字幕</span>
                  <span className="text-slate-500 text-sm">(E)</span>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-400" />
              </button>

              {showExportSubmenu && (
                <div className="absolute left-full top-0 ml-1 w-48 bg-slate-800 border border-slate-600 rounded-lg shadow-xl overflow-hidden">
                  <button className="w-full px-4 py-2.5 hover:bg-slate-700 transition-colors text-left text-sm">
                    SRT 格式
                  </button>
                  <button className="w-full px-4 py-2.5 hover:bg-slate-700 transition-colors text-left text-sm">
                    VTT 格式
                  </button>
                  <button className="w-full px-4 py-2.5 hover:bg-slate-700 transition-colors text-left text-sm">
                    TXT 格式
                  </button>
                </div>
              )}
            </div>

            <div className="h-px bg-slate-600 my-1"></div>

            <button className="w-full px-4 py-2.5 hover:bg-slate-700 transition-colors flex items-center justify-between text-left">
              <div className="flex items-center gap-3">
                <span className="text-sm">退出</span>
                <span className="text-slate-500 text-sm">(X)</span>
              </div>
              <span className="text-xs text-slate-400">Ctrl+Q</span>
            </button>
          </div>
        )}
      </div>

      {/* 幫助 Menu */}
      <div className="relative">
        <button
          onClick={() => toggleMenu('help')}
          className="px-3 py-1.5 hover:bg-slate-700/50 rounded transition-colors text-sm"
        >
          幫助<span className="text-slate-500">(H)</span>
        </button>

        {activeMenu === 'help' && (
          <div className="absolute top-full left-0 mt-1 w-56 bg-slate-800 border border-slate-600 rounded-lg shadow-xl z-50 overflow-hidden">
            <button className="w-full px-4 py-2.5 hover:bg-slate-700 transition-colors text-left text-sm">
              使用說明
            </button>
            <button className="w-full px-4 py-2.5 hover:bg-slate-700 transition-colors text-left text-sm">
              快捷鍵
            </button>
            <div className="h-px bg-slate-600 my-1"></div>
            <button className="w-full px-4 py-2.5 hover:bg-slate-700 transition-colors text-left text-sm">
              關於 Canto-beats
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
