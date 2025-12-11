import { Undo2, Redo2, Scissors, Move, Copy, Trash2, Plus, Minus, Layers, Video, Volume2 } from 'lucide-react';
import { useState } from 'react';

export function TimelineSection() {
  const [zoom, setZoom] = useState(50);
  const [currentTime, setCurrentTime] = useState(5);

  const subtitleBlocks = [
    { id: 1, start: 0, duration: 5, text: 'Canto-beats', color: 'bg-slate-700' },
    { id: 2, start: 5, duration: 3, text: '開始 AI 轉寫', color: 'bg-cyan-500' },
    { id: 3, start: 8, duration: 4, text: '字幕風格', color: 'bg-slate-700' },
    { id: 4, start: 12, duration: 3, text: '英文處理', color: 'bg-slate-700' },
    { id: 5, start: 15, duration: 5, text: '數天格式', color: 'bg-slate-700' },
  ];

  return (
    <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-4">
      {/* Toolbar */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <button className="p-2 hover:bg-slate-700 rounded-lg transition-colors">
            <Undo2 className="w-4 h-4" />
          </button>
          <button className="p-2 hover:bg-slate-700 rounded-lg transition-colors">
            <Redo2 className="w-4 h-4" />
          </button>
          <div className="w-px h-6 bg-slate-600 mx-1"></div>
          <button className="p-2 hover:bg-slate-700 rounded-lg transition-colors">
            <Scissors className="w-4 h-4" />
          </button>
          <button className="p-2 hover:bg-slate-700 rounded-lg transition-colors">
            <Move className="w-4 h-4" />
          </button>
          <button className="p-2 hover:bg-slate-700 rounded-lg transition-colors">
            <Copy className="w-4 h-4" />
          </button>
          <button className="p-2 hover:bg-slate-700 rounded-lg transition-colors">
            <Trash2 className="w-4 h-4" />
          </button>
        </div>

        <div className="flex items-center gap-3">
          <button className="flex items-center gap-2 px-3 py-1.5 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors text-sm">
            <Plus className="w-4 h-4" />
            <span>添加字幕</span>
          </button>
          <button className="p-2 hover:bg-slate-700 rounded-lg transition-colors">
            <Plus className="w-4 h-4" />
          </button>
          <div className="flex items-center gap-2 bg-slate-700 rounded-lg px-3 py-1.5">
            <input
              type="range"
              min="0"
              max="100"
              value={zoom}
              onChange={(e) => setZoom(parseInt(e.target.value))}
              className="w-24 h-1 bg-slate-600 rounded-lg appearance-none cursor-pointer"
            />
          </div>
          <button className="p-2 hover:bg-slate-700 rounded-lg transition-colors">
            <Minus className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Time Ruler */}
      <div className="relative mb-2">
        <div className="flex text-xs text-slate-400 mb-1">
          <div className="w-20 text-center">00:00:00</div>
          <div className="flex-1 flex justify-between px-4">
            {[0, 5, 10, 15, 20, 25, 30].map((time) => (
              <div key={time} className="relative">
                <div className="absolute -left-4">00:00:{time.toString().padStart(2, '0')}</div>
                <div className="w-px h-2 bg-slate-600"></div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Timeline Tracks */}
      <div className="space-y-2">
        {/* Subtitle Track */}
        <div className="flex items-start gap-2">
          <div className="w-20 flex items-center gap-2 py-2">
            <Layers className="w-4 h-4 text-slate-400" />
            <span className="text-sm text-slate-400">字幕層次</span>
          </div>
          <div className="flex-1 bg-slate-900/50 rounded-lg p-2 min-h-[80px] relative">
            <div className="relative h-16">
              {subtitleBlocks.map((block) => (
                <div
                  key={block.id}
                  className={`absolute top-0 h-full ${block.color} rounded border border-slate-600 px-2 py-1 text-xs flex items-center justify-center cursor-move hover:brightness-110 transition-all`}
                  style={{
                    left: `${(block.start / 30) * 100}%`,
                    width: `${(block.duration / 30) * 100}%`,
                  }}
                >
                  <span className="truncate">{block.text}</span>
                </div>
              ))}
              {/* Playhead */}
              <div
                className="absolute top-0 bottom-0 w-0.5 bg-cyan-400 z-10"
                style={{ left: `${(currentTime / 30) * 100}%` }}
              >
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-3 h-3 bg-cyan-400 rounded-sm"></div>
              </div>
            </div>
          </div>
        </div>

        {/* Video Track */}
        <div className="flex items-start gap-2">
          <div className="w-20 flex items-center gap-2 py-2">
            <Video className="w-4 h-4 text-slate-400" />
            <span className="text-sm text-slate-400">視頻</span>
          </div>
          <div className="flex-1 bg-slate-900/50 rounded-lg p-2 min-h-[60px] relative">
            <div className="relative h-12">
              <div className="absolute top-0 left-0 h-full w-full rounded overflow-hidden">
                {/* Video thumbnail strip */}
                <div className="flex h-full">
                  {Array.from({ length: 6 }).map((_, i) => (
                    <div
                      key={i}
                      className="flex-1 bg-gradient-to-br from-slate-700 to-slate-800 border-r border-slate-600"
                    >
                      <div className="w-full h-full opacity-30 bg-cyan-500/10"></div>
                    </div>
                  ))}
                </div>
              </div>
              {/* Playhead */}
              <div
                className="absolute top-0 bottom-0 w-0.5 bg-cyan-400 z-10"
                style={{ left: `${(currentTime / 30) * 100}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* Volume Track */}
        <div className="flex items-start gap-2">
          <div className="w-20 flex items-center gap-2 py-2">
            <Volume2 className="w-4 h-4 text-slate-400" />
            <span className="text-sm text-slate-400">音頻</span>
          </div>
          <div className="flex-1 bg-slate-900/50 rounded-lg p-2 min-h-[60px] relative">
            <div className="relative h-12">
              {/* Waveform */}
              <div className="flex items-end h-full gap-px">
                {Array.from({ length: 120 }).map((_, i) => {
                  const height = Math.random() * 100;
                  return (
                    <div
                      key={i}
                      className="flex-1 bg-cyan-500/50 rounded-t"
                      style={{ height: `${height}%` }}
                    ></div>
                  );
                })}
              </div>
              {/* Playhead */}
              <div
                className="absolute top-0 bottom-0 w-0.5 bg-cyan-400 z-10"
                style={{ left: `${(currentTime / 30) * 100}%` }}
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
