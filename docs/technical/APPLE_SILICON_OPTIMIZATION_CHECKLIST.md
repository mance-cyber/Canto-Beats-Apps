# 🚀 Apple Silicon 優化實施清單

## ✅ Phase 1: 緊急修復（預計 1-2 天）

### 任務 1.1: 修復 MPS VRAM 檢測
- [ ] **文件**: `src/core/hardware_detector.py`
- [ ] **行數**: 153-170
- [ ] **變更**: 
  - 添加 `psutil` 依賴到 `requirements-macos-silicon.txt`
  - 計算統一內存的 70% 作為有效 VRAM
  - 更新日誌輸出顯示實際可用內存
- [ ] **測試**: 
  ```bash
  python -c "from src.core.hardware_detector import HardwareDetector; print(HardwareDetector().detect())"
  ```
- [ ] **預期結果**: M1/M2/M3 Mac 應顯示 `MAINSTREAM` 或 `ULTIMATE` tier

---

### 任務 1.2: 啟用 LLM MPS 設備映射
- [ ] **文件**: `src/models/qwen_llm.py`
- [ ] **行數**: 100-136
- [ ] **變更**:
  - 創建 `get_device_map()` 輔助函數
  - 支持 `device_map="mps"` 參數
  - 為 MPS 設備啟用 FP16 精度
  - 禁用 MPS 上的 `bitsandbytes` 量化（僅 CUDA 支持）
- [ ] **測試**:
  ```bash
  python test_qwen_mps.py  # 需創建測試腳本
  ```
- [ ] **預期結果**: Qwen2.5-7B 在 MPS 上加載並推理成功

---

## 🔥 Phase 2: 核心優化（預計 1 週）

### 任務 2.1: VideoToolbox 視頻編碼
- [ ] **文件**: `src/utils/video_utils.py`
- [ ] **新增函數**: `get_optimal_video_encoder()`
- [ ] **變更**:
  - 檢測平台並返回最佳編碼器配置
  - macOS: `h264_videotoolbox` / `hevc_videotoolbox`
  - CUDA: `h264_nvenc`
  - CPU: `libx264` 回退
- [ ] **集成位置**:
  - `src/pipeline/subtitle_pipeline_v2.py` (視頻導出)
  - `src/ui/timeline_editor.py` (時間軸渲染)
- [ ] **測試**:
  ```bash
  ffmpeg -f lavfi -i testsrc=duration=10:size=1920x1080:rate=30 \
         -c:v h264_videotoolbox -b:v 5M test_videotoolbox.mp4
  ```

---

### 任務 2.2: Accelerate Framework 音頻處理
- [ ] **文件**: `src/utils/audio_utils.py`
- [ ] **新增類**: `AccelerateAudioProcessor`
- [ ] **變更**:
  - 使用 `vDSP` 進行音頻重採樣
  - 使用 `vDSP_vgenp` 進行向量插值
  - 回退到 NumPy（非 macOS 平台）
- [ ] **集成位置**:
  - `src/models/vad_processor.py` (VAD 預處理)
  - `src/pipeline/subtitle_pipeline_v2.py` (音頻提取)
- [ ] **測試**:
  ```python
  # 性能對比測試
  import time
  audio = np.random.randn(48000 * 60)  # 1 分鐘音頻
  
  # NumPy 版本
  start = time.time()
  resampled_numpy = resample_numpy(audio, 48000, 16000)
  print(f"NumPy: {time.time() - start:.3f}s")
  
  # Accelerate 版本
  start = time.time()
  resampled_vdsp = resample_vdsp(audio, 48000, 16000)
  print(f"vDSP: {time.time() - start:.3f}s")
  ```

---

## 🎨 Phase 3: 進階優化（預計 2 週）

### 任務 3.1: Core Image GPU 渲染
- [ ] **文件**: `src/ui/utils/waveform_renderer.py`
- [ ] **新增類**: `CoreImageWaveformRenderer`
- [ ] **變更**:
  - 使用 `CIContext` 創建 Metal-backed 渲染上下文
  - 使用 `CIFilter` 進行 GPU 加速繪圖
  - 回退到 PIL（非 macOS 平台）
- [ ] **依賴**: 
  ```bash
  pip install pyobjc-framework-Quartz pyobjc-framework-CoreImage
  ```
- [ ] **測試**: 在時間軸編輯器中加載長視頻，觀察波形渲染速度

---

### 任務 3.2: MPS 批量推理優化
- [ ] **文件**: `src/models/whisper_asr.py`
- [ ] **新增函數**: `batch_transcribe_mps()`
- [ ] **變更**:
  - 將多個音頻段打包成 batch tensor
  - 使用 `torch.stack()` 並移動到 MPS 設備
  - 批量調用 Whisper 模型
- [ ] **測試**: 對比單句 vs 批量推理的吞吐量

---

## 🧪 測試計劃

### 單元測試
```bash
# 創建測試文件
touch tests/test_mps_optimization.py
touch tests/test_videotoolbox.py
touch tests/test_accelerate_audio.py
```

### 性能基準測試
```python
# tests/benchmark_apple_silicon.py
import time
import torch
from src.core.hardware_detector import HardwareDetector
from src.models.qwen_llm import QwenLLM

def benchmark_llm_inference():
    detector = HardwareDetector()
    profile = detector.detect()
    
    llm = QwenLLM(config, profile)
    llm.load_models()
    
    test_sentences = ["呢個係測試句子"] * 10
    
    start = time.time()
    for sentence in test_sentences:
        llm.process_sentence(sentence)
    elapsed = time.time() - start
    
    print(f"Device: {profile.device}")
    print(f"Total time: {elapsed:.2f}s")
    print(f"Avg per sentence: {elapsed/len(test_sentences):.2f}s")
```

---

## 📊 驗收標準

| 指標 | 優化前 | 目標 | 驗收方法 |
|-----|-------|------|---------|
| LLM 推理速度 (M2 Max) | 20s/句 | <4s/句 | `benchmark_llm_inference()` |
| 視頻編碼速度 (1080p) | 0.5x 實時 | >2x 實時 | FFmpeg 編碼 10 分鐘視頻 |
| 音頻重採樣速度 | 1.0x | >2x | `benchmark_audio_resample()` |
| GPU 利用率 | <20% | >60% | Activity Monitor > GPU History |
| 功耗（平均） | 25W | <18W | `sudo powermetrics --samplers cpu_power` |

---

## 🐛 已知問題與限制

### MPS 限制
1. **不支持 INT8 量化**: `bitsandbytes` 僅支持 CUDA
   - **解決方案**: 使用 FP16 或等待 Apple 官方支持
2. **部分算子未實現**: 某些 PyTorch 算子在 MPS 上會回退到 CPU
   - **解決方案**: 使用 `torch.mps.is_available()` 檢測並提供回退

### VideoToolbox 限制
1. **僅支持 H.264/HEVC**: 不支持 VP9/AV1
2. **質量控制有限**: 比特率控制不如 x264 精細

---

## 📝 文檔更新

- [ ] 更新 `MACOS_SILICON_BUILD_GUIDE.md`
- [ ] 更新 `MACOS_TECHNICAL_NOTES.md`
- [ ] 創建 `APPLE_SILICON_PERFORMANCE_TUNING.md`
- [ ] 更新 `README.md` 添加性能對比表

---

**創建時間**: 2025-01-XX  
**負責人**: Development Team  
**預計完成**: Phase 1-3 共 3-4 週

