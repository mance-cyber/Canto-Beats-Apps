"""
Unit tests for AI model components.
"""

import unittest
import torch
from pathlib import Path

# Note: These tests require actual audio files to run
# For automated testing, consider using synthetic audio or mocking


class TestModelManager(unittest.TestCase):
    """Test ModelManager base class."""
    
    def test_device_detection(self):
        """Test automatic device detection."""
        from core.config import Config
        from models.model_manager import ModelManager
        
        config = Config()
        
        # Create a concrete subclass for testing
        class TestModel(ModelManager):
            def load_model(self):
                pass
            def unload_model(self):
                pass
        
        manager = TestModel(config)
        
        # Check device is valid
        self.assertIn(manager.device.type, ['cpu', 'cuda', 'mps'])
        
        # Check device info
        info = manager.get_device_info()
        self.assertIn('device_type', info)
        self.assertIn('gpu_available', info)


class TestWhisperASR(unittest.TestCase):
    """Test WhisperASR integration."""
    
    @unittest.skipIf(not Path('test_audio.wav').exists(), "No test audio file")
    def test_model_loading(self):
        """Test Whisper model loading."""
        from core.config import Config
        from models.whisper_asr import WhisperASR
        
        config = Config()
        asr = WhisperASR(config, model_size='tiny')  # Use tiny for faster testing
        
        # Test loading
        asr.load_model()
        self.assertTrue(asr.is_loaded)
        
        # Test cleanup
        asr.cleanup()
        self.assertFalse(asr.is_loaded)
    
    @unittest.skipIf(not Path('test_audio.wav').exists(), "No test audio file")
    def test_transcription(self):
        """Test audio transcription."""
        from core.config import Config
        from models.whisper_asr import WhisperASR
        
        config = Config()
        asr = WhisperASR(config, model_size='tiny')
        asr.load_model()
        
        # Transcribe
        result = asr.transcribe('test_audio.wav')
        
        self.assertIn('text', result)
        self.assertIn('segments', result)
        self.assertIn('language', result)
        self.assertGreater(len(result['segments']), 0)
        
        asr.cleanup()


class TestVADProcessor(unittest.TestCase):
    """Test VADProcessor."""
    
    @unittest.skipIf(not Path('test_audio.wav').exists(), "No test audio file")
    def test_vad_loading(self):
        """Test VAD model loading."""
        from core.config import Config
        from models.vad_processor import VADProcessor
        
        config = Config()
        vad = VADProcessor(config)
        
        # Test loading
        vad.load_model()
        self.assertTrue(vad.is_loaded)
        
        # Test cleanup
        vad.cleanup()
        self.assertFalse(vad.is_loaded)
    
    @unittest.skipIf(not Path('test_audio.wav').exists(), "No test audio file")
    def test_voice_detection(self):
        """Test voice segment detection."""
        from core.config import Config
        from models.vad_processor import VADProcessor
        
        config = Config()
        vad = VADProcessor(config)
        vad.load_model()
        
        # Detect voice
        segments = vad.detect_voice_segments('test_audio.wav')
        
        self.assertIsInstance(segments, list)
        # Should have at least one voice segment
        if len(segments) > 0:
            self.assertGreater(segments[0].end, segments[0].start)
        
        vad.cleanup()


class TestAudioPreprocessor(unittest.TestCase):
    """Test audio preprocessing utilities."""
    
    def test_validation(self):
        """Test audio file validation."""
        from utils.audio_utils import AudioPreprocessor
        
        # Invalid file
        self.assertFalse(AudioPreprocessor.validate_audio_file('nonexistent.wav'))
        
        # Unsupported format
        self.assertFalse(AudioPreprocessor.validate_audio_file('test.xyz'))
    
    @unittest.skipIf(not Path('test_audio.wav').exists(), "No test audio file")
    def test_audio_loading(self):
        """Test audio loading and preprocessing."""
        from utils.audio_utils import AudioPreprocessor
        
        waveform, sr = AudioPreprocessor.load_audio('test_audio.wav')
        
        # Check sample rate
        self.assertEqual(sr, 16000)  # Should be resampled to 16kHz
        
        # Check waveform is tensor
        self.assertIsInstance(waveform, torch.Tensor)
        
        # Check normalization
        self.assertLessEqual(torch.max(torch.abs(waveform)).item(), 1.0)


if __name__ == '__main__':
    unittest.main()
