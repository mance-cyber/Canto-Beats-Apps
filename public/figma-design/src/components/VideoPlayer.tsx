import { Play, Pause, SkipBack, SkipForward, Volume2, Maximize, RotateCcw } from 'lucide-react';
import { useState, useRef } from 'react';

export function VideoPlayer() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(180); // 3 minutes in seconds
  const videoRef = useRef<HTMLVideoElement>(null);

  const togglePlay = () => {
    setIsPlaying(!isPlaying);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleProgressChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newTime = parseFloat(e.target.value);
    setCurrentTime(newTime);
  };

  return (
    <div className="bg-slate-800/50 rounded-xl border border-slate-700 overflow-hidden">
      {/* Video Display Area */}
      <div className="aspect-video bg-gradient-to-br from-slate-900 to-slate-800 relative">
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-slate-600 text-6xl">▶</div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="px-4 pt-4 pb-2">
        <input
          type="range"
          min="0"
          max={duration}
          value={currentTime}
          onChange={handleProgressChange}
          className="w-full h-1 bg-slate-700 rounded-lg appearance-none cursor-pointer slider"
          style={{
            background: `linear-gradient(to right, #06b6d4 0%, #06b6d4 ${(currentTime / duration) * 100}%, #334155 ${(currentTime / duration) * 100}%, #334155 100%)`
          }}
        />
      </div>

      {/* Controls */}
      <div className="px-4 pb-4 flex items-center justify-between">
        <div className="flex items-center gap-1">
          <span className="text-sm text-slate-400">
            {formatTime(currentTime)} / {formatTime(duration)}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button className="p-2 hover:bg-slate-700 rounded-lg transition-colors">
            <SkipBack className="w-4 h-4" />
          </button>
          <button className="p-2 hover:bg-slate-700 rounded-lg transition-colors">
            <RotateCcw className="w-4 h-4" />
          </button>
          <button
            onClick={togglePlay}
            className="p-3 bg-cyan-500 hover:bg-cyan-600 rounded-lg transition-colors"
          >
            {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
          </button>
          <button className="p-2 hover:bg-slate-700 rounded-lg transition-colors">
            <SkipForward className="w-4 h-4" />
          </button>
          <button className="p-2 hover:bg-slate-700 rounded-lg transition-colors">
            <SkipForward className="w-4 h-4" />
          </button>
        </div>

        <div className="flex items-center gap-2">
          <button className="p-2 hover:bg-slate-700 rounded-lg transition-colors">
            <Volume2 className="w-4 h-4" />
          </button>
          <button className="p-2 hover:bg-slate-700 rounded-lg transition-colors">
            <RotateCcw className="w-4 h-4" />
          </button>
          <button className="p-2 hover:bg-slate-700 rounded-lg transition-colors">
            <Maximize className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
