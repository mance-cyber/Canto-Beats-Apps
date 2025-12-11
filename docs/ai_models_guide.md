# AI Models Usage Guide

## Overview

The Canto-beats AI system provides professional-grade Cantonese speech recognition and intelligent sentence segmentation using:

- **Whisper ASR**: OpenAI's Whisper model for accurate Cantonese transcription
- **Silero VAD**: Advanced voice activity detection for smart sentence boundaries
- **Audio Processing**: Automatic preprocessing and format conversion

---

## Quick Start

### Basic Transcription

```python
from core.config import Config
from models.whisper_asr import WhisperASR

# Initialize
config = Config()
asr = WhisperASR(config, model_size='medium')
asr.load_model()

# Transcribe
result = asr.transcribe('your_audio.wav')

print(result['text'])  # Full transcription
for seg in result['segments']:
    print(f"[{seg.start:.2f}s - {seg.end:.2f}s] {seg.text}")

asr.cleanup()
```

### Voice Activity Detection

```python
from core.config import Config
from models.vad_processor import VADProcessor

# Initialize
config = Config()
vad = VADProcessor(config, threshold=0.5)
vad.load_model()

# Detect voice segments
segments = vad.detect_voice_segments('audio.wav')

for seg in segments:
    print(f"Voice: {seg.start:.2f}s - {seg.end:.2f}s")

# Get speech ratio
ratio = vad.get_speech_ratio('audio.wav')
print(f"Speech ratio: {ratio:.2%}")

vad.cleanup()
```

### Complete Pipeline

```python
from core.config import Config
from models.whisper_asr import WhisperASR
from models.vad_processor import VADProcessor

config = Config()

# Initialize models
asr = WhisperASR(config)
vad = VADProcessor(config)

asr.load_model()
vad.load_model()

# Transcribe
transcription = asr.transcribe('audio.wav', language='zh')

# Detect voice
voice_segments = vad.detect_voice_segments('audio.wav')

# Merge for optimal segments
merged = vad.merge_with_transcription(
    transcription['segments'],
    voice_segments,
    max_gap=1.0
)

# Cleanup
asr.cleanup()
vad.cleanup()
```

---

## Model Sizes

### Whisper Models

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| `tiny` | ~75 MB | Very Fast | 80% | Testing only |
| `base` | ~150 MB | Fast | 85% | Quick drafts |
| `small` | ~500 MB | Medium | 90% | General use |
| `medium` | ~1.5 GB | Slow | 95%+ | **Lite version** |
| `large-v3` | ~3 GB | Very Slow | 98.5% | **Flagship version** |

### Device Selection

The system automatically detects the best available device:

1. **CUDA** (NVIDIA GPU) - Fastest
2. **MPS** (Apple Silicon) - Fast
3. **CPU** - Slowest but always available

Override in config:
```python
config.set('use_gpu', False)  # Force CPU
```

---

## Configuration

### AI Model Settings

Edit `config.json` or use programmatically:

```python
config = Config()

# Whisper settings
config.set('whisper_model', 'large-v3')  # Model size
config.set('default_language', 'zh')     # Cantonese
config.set('enable_word_timestamps', True)
config.set('beam_size', 5)               # Accuracy vs speed

# VAD settings
config.set('vad_threshold', 0.5)         # Sensitivity (0.0-1.0)
config.set('min_silence_duration_ms', 500)  # Min silence to split
config.set('min_speech_duration_ms', 250)   # Min speech duration

# Performance
config.set('use_gpu', True)
config.set('chunk_audio', True)          # For long audio
config.set('max_audio_chunk_s', 30.0)
```

---

## Advanced Features

### Language Detection

```python
asr = WhisperASR(config)
asr.load_model()

detected_lang = asr.detect_language('audio.wav')
print(f"Detected: {detected_lang}")

# Use detected language for transcription
result = asr.transcribe('audio.wav', language=detected_lang)
```

### Custom Prompts (Cantonese Optimization)

```python
# Add custom prompt to guide recognition
result = asr.transcribe(
    'audio.wav',
    language='zh',
    initial_prompt='以下是粤语对话，包含专业术语。'
)
```

### Silence Removal

```python
vad = VADProcessor(config)
vad.load_model()

# Remove silence and save
clean_audio = vad.remove_silence('audio.wav', 'clean_audio.wav')
```

### Audio Preprocessing

```python
from utils.audio_utils import AudioPreprocessor

# Load and preprocess
waveform, sr = AudioPreprocessor.load_audio('audio.mp3')
print(f"Loaded: {len(waveform)} samples at {sr}Hz")

# Extract audio from video
audio_path = AudioPreprocessor.extract_audio_from_video('video.mp4')

# Chunk long audio
chunks = AudioPreprocessor.chunk_audio(waveform, sr, chunk_length_s=30.0)
```

---

## Performance Tips

### 1. Choose Right Model Size

- Development/Testing: Use `tiny` or `base`
- Production (Lite): Use `medium`
- Production (Flagship): Use `large-v3`

### 2. Enable GPU

Ensure PyTorch with CUDA/MPS support is installed:

```bash
# NVIDIA CUDA
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# Apple Silicon
pip install torch torchaudio  # MPS support built-in
```

### 3. Optimize VAD Threshold

Lower threshold = More sensitive (may include noise)
Higher threshold = Less sensitive (may miss quiet speech)

Recommended ranges:
- Clean audio: 0.6-0.7
- Noisy audio: 0.4-0.5

### 4. Batch Processing

For multiple files, reuse loaded models:

```python
asr = WhisperASR(config)
asr.load_model()  # Load once

for file in audio_files:
    result = asr.transcribe(file)
    process_result(result)

asr.cleanup()  # Cleanup once
```

---

## Troubleshooting

### Model Download Issues

Models are auto-downloaded on first use. If downloads fail:

1. Check internet connection
2. Verify cache directory: `config.get('models_dir')`
3. Manually download models to cache directory

### Out of Memory (GPU)

If you encounter OOM errors:

1. Use smaller model size
2. Enable audio chunking
3. Reduce `max_audio_chunk_s`
4. Fallback to CPU: `config.set('use_gpu', False)`

### Poor Recognition Quality

1. Check audio quality (clear, minimal noise)
2. Use larger model (`large-v3`)
3. Provide custom prompt with context
4. Verify language is set to `'zh'` for Cantonese

---

## API Reference

See individual module documentation:

- [`models/model_manager.py`](../src/models/model_manager.py) - Base model management
- [`models/whisper_asr.py`](../src/models/whisper_asr.py) - Whisper ASR wrapper
- [`models/vad_processor.py`](../src/models/vad_processor.py) - VAD processor
- [`utils/audio_utils.py`](../src/utils/audio_utils.py) - Audio utilities

---

## Examples

Complete examples are in the [`examples/`](../examples/) directory:

- `ai_pipeline_demo.py` - Full pipeline demonstration

Run the demo:

```bash
python examples/ai_pipeline_demo.py your_audio.wav medium
```

---

## Support

For issues or questions, check:

1. This documentation
2. Unit tests in `tests/test_models.py`
3. Example scripts in `examples/`
