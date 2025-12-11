# 🚀 AI Models Quick Start

## Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **For GPU support (recommended):**

**NVIDIA CUDA:**
```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**Apple Silicon (M1/M2/M3):**
```bash
pip install torch torchaudio  # MPS support built-in
```

---

## Basic Usage

### 1️⃣ Transcribe Audio

```python
from core.config import Config
from models.whisper_asr import WhisperASR

# Setup
config = Config()
asr = WhisperASR(config, model_size='medium')
asr.load_model()

# Transcribe
result = asr.transcribe('your_audio.wav', language='zh')

# Results
print(result['text'])  # Full transcription
for seg in result['segments']:
    print(f"[{seg.start:.2f}s] {seg.text}")

# Cleanup
asr.cleanup()
```

### 2️⃣ Voice Activity Detection

```python
from core.config import Config
from models.vad_processor import VADProcessor

# Setup
config = Config()
vad = VADProcessor(config)
vad.load_model()

# Detect voice
segments = vad.detect_voice_segments('audio.wav')

for seg in segments:
    print(f"Voice: {seg.start:.2f}s - {seg.end:.2f}s")

vad.cleanup()
```

### 3️⃣ Complete Pipeline

Run the demo script:

```bash
python examples/ai_pipeline_demo.py your_video.mp4
```

Or use programmatically:

```python
from core.config import Config
from models.whisper_asr import WhisperASR
from models.vad_processor import VADProcessor

config = Config()
asr = WhisperASR(config)
vad = VADProcessor(config)

asr.load_model()
vad.load_model()

# Transcribe
transcription = asr.transcribe('audio.wav', language='zh')

# Detect voice
voice_segments = vad.detect_voice_segments('audio.wav')

# Merge
final = vad.merge_with_transcription(
    transcription['segments'],
    voice_segments
)

# Use final segments...
for seg in final:
    print(f"[{seg.start:.2f}-{seg.end:.2f}] {seg.text}")

asr.cleanup()
vad.cleanup()
```

---

## Model Sizes

| Model | Size | Speed | Best For |
|-------|------|-------|----------|
| `tiny` | 75 MB | ⚡⚡⚡ | Testing |
| `medium` | 1.5 GB | ⚡⚡ | **Lite version** |
| `large-v3` | 3 GB | ⚡ | **Flagship version** |

---

## Configuration

### Quick Config

```python
from core.config import Config

config = Config()

# Model selection
config.set('whisper_model', 'medium')  # or 'large-v3'
config.set('build_type', 'lite')       # or 'flagship'

# Performance
config.set('use_gpu', True)            # Auto-detect GPU

# VAD sensitivity
config.set('vad_threshold', 0.5)       # 0.0-1.0

# Language
config.set('default_language', 'zh')   # Cantonese
```

### Config File

Edit `%APPDATA%/Canto-beats/config.json`:

```json
{
  "whisper_model": "medium",
  "vad_threshold": 0.5,
  "use_gpu": true,
  "default_language": "zh"
}
```

---

## Testing

### Run Tests

```bash
# All tests
pytest tests/ -v

# Specific tests
pytest tests/test_models.py -v
```

### Manual Testing

```bash
# Test Whisper
python -m src.models.whisper_asr test_audio.wav

# Test VAD
python -m src.models.vad_processor test_audio.wav

# Test Audio Utils
python -m src.utils.audio_utils test_audio.mp3
```

---

## Troubleshooting

### "Out of memory" error
→ Use smaller model or disable GPU:
```python
config.set('whisper_model', 'medium')
config.set('use_gpu', False)
```

### Model download slow
→ Models auto-download on first use. Be patient or manually download.

### Poor recognition quality
→ Use larger model + verify audio is Cantonese:
```python
config.set('whisper_model', 'large-v3')
```

---

## Next Steps

📖 **Full Documentation:** [`docs/ai_models_guide.md`](../docs/ai_models_guide.md)

🧪 **Examples:** [`examples/ai_pipeline_demo.py`](../examples/ai_pipeline_demo.py)

🧩 **Integration:** See `walkthrough.md` for integration with main app

---

## Support

- Check [`docs/ai_models_guide.md`](../docs/ai_models_guide.md) for detailed usage
- Review unit tests in [`tests/test_models.py`](../tests/test_models.py)
- Run demo: `python examples/ai_pipeline_demo.py <audio_file>`
