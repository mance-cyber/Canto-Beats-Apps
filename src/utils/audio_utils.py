"""
Audio preprocessing utilities for AI models.
"""

import os
import sys
import numpy as np
from pathlib import Path
from typing import Union, Optional, Tuple, List
import torch
import torchaudio
from utils.logger import setup_logger


logger = setup_logger()


class AudioPreprocessor:
    """Audio preprocessing for AI models (Whisper, VAD)"""
    
    # Whisper requires 16kHz mono audio
    TARGET_SAMPLE_RATE = 16000
    
    # Supported audio formats
    SUPPORTED_FORMATS = {
        '.mp3', '.wav', '.flac', '.m4a', '.aac', 
        '.ogg', '.opus', '.wma', '.mp4', '.mkv'
    }
    
    @staticmethod
    def validate_audio_file(file_path: Union[str, Path]) -> bool:
        """
        Validate if file exists and is a supported audio format.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            True if valid, False otherwise
        """
        path = Path(file_path)
        
        if not path.exists():
            logger.error(f"Audio file not found: {file_path}")
            return False
        
        if path.suffix.lower() not in AudioPreprocessor.SUPPORTED_FORMATS:
            logger.error(f"Unsupported audio format: {path.suffix}")
            return False
        
        return True
    
    @staticmethod
    def load_audio(
        file_path: Union[str, Path],
        target_sr: int = TARGET_SAMPLE_RATE,
        normalize: bool = True
    ) -> Tuple[torch.Tensor, int]:
        """
        Load audio file and resample to target sample rate.
        
        Args:
            file_path: Path to audio file
            target_sr: Target sample rate (default: 16000 for Whisper)
            normalize: Whether to normalize audio to [-1, 1]
            
        Returns:
            Tuple of (audio_tensor, sample_rate)
        """
        if not AudioPreprocessor.validate_audio_file(file_path):
            raise ValueError(f"Invalid audio file: {file_path}")

        logger.info(f"Loading audio: {file_path}")
        
        # Check if file is a video format - extract audio first
        file_path = Path(file_path)
        video_formats = {'.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv'}
        
        if file_path.suffix.lower() in video_formats:
            logger.info(f"Detected video format {file_path.suffix}, extracting audio with FFmpeg...")
            try:
                # Extract audio to temporary WAV file
                temp_audio = file_path.with_suffix('.temp.wav')
                AudioPreprocessor.extract_audio_from_video(file_path, temp_audio)
                file_path = temp_audio
            except Exception as e:
                logger.error(f"Failed to extract audio from video: {e}", exc_info=True)
                raise RuntimeError(f"無法從影片提取音頻: {e}")

        # Load audio using torchaudio (with fallback for torchcodec error)
        try:
            waveform, sample_rate = torchaudio.load(str(file_path), backend="soundfile")
        except Exception as e:
            logger.debug(f"torchaudio.load with soundfile backend failed: {e}, trying default")
            try:
                waveform, sample_rate = torchaudio.load(str(file_path))
            except ImportError as ie:
                if "torchcodec" in str(ie):
                    # Fallback to soundfile directly
                    logger.info("Using soundfile fallback due to torchcodec error")
                    import soundfile as sf
                    data, sample_rate = sf.read(str(file_path))
                    waveform = torch.from_numpy(data).float().T
                    if waveform.dim() == 1:
                        waveform = waveform.unsqueeze(0)
                else:
                    raise
        
        
        # Convert to mono if stereo
        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)
            logger.debug("Converted stereo to mono")
        
        # Resample if needed
        if sample_rate != target_sr:
            resampler = torchaudio.transforms.Resample(
                orig_freq=sample_rate,
                new_freq=target_sr
            )
            waveform = resampler(waveform)
            logger.debug(f"Resampled from {sample_rate}Hz to {target_sr}Hz")
            sample_rate = target_sr
        
        # Normalize audio
        if normalize:
            waveform = waveform / torch.max(torch.abs(waveform))
            logger.debug("Normalized audio to [-1, 1]")
        
        logger.info(f"Audio loaded: {waveform.shape[1] / sample_rate:.2f}s duration")
        
        return waveform.squeeze(0), sample_rate
    
    @staticmethod
    def extract_audio_from_video(
        video_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None
    ) -> Path:
        """
        Extract audio from video file using ffmpeg.
        
        Args:
            video_path: Path to video file
            output_path: Optional output path for extracted audio
            
        Returns:
            Path to extracted audio file
        """
        video_path = Path(video_path)
        
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Default output path
        if output_path is None:
            output_path = video_path.with_suffix('.wav')
        else:
            output_path = Path(output_path)
        
        logger.info(f"Extracting audio from video: {video_path}")
        
        try:
            import av  # PyAV provides FFmpeg functionality without external binary
            
            # Open video file with PyAV
            container = av.open(str(video_path))
            
            # Get audio stream
            audio_stream = container.streams.audio[0]
            
            # Extract and decode audio frames
            audio_frames = []
            for frame in container.decode(audio_stream):
                # Convert frame to numpy array
                audio_frames.append(frame.to_ndarray())
            
            container.close()
            
            if not audio_frames:
                raise RuntimeError("No audio frames found in video")
            
            # Concatenate all frames
            import numpy as np
            audio_data = np.concatenate(audio_frames, axis=1)
            
            # Convert to PyTorch tensor and save as WAV
            import soundfile as sf
            
            # PyAV returns float data, soundfile expects it in range [-1, 1]
            # Resample to target sample rate if needed
            if audio_stream.rate != AudioPreprocessor.TARGET_SAMPLE_RATE:
                import scipy.signal
                num_samples = int(len(audio_data[0]) * AudioPreprocessor.TARGET_SAMPLE_RATE / audio_stream.rate)
                audio_data = scipy.signal.resample(audio_data, num_samples, axis=1)
                sample_rate = AudioPreprocessor.TARGET_SAMPLE_RATE
            else:
                sample_rate = audio_stream.rate
            
            # Convert to mono if stereo
            if audio_data.shape[0] > 1:
                audio_data = np.mean(audio_data, axis=0)
            else:
                audio_data = audio_data[0]
            
            # Save as WAV
            sf.write(str(output_path), audio_data, sample_rate, subtype='PCM_16')
            
            logger.info(f"Audio extracted to: {output_path}")
            return output_path
            
        except ImportError as e:
            logger.error(f"Required library not available: {e}")
            logger.error("Please ensure av (PyAV), soundfile, and scipy are installed")
            raise
        except Exception as e:
            logger.error(f"Failed to extract audio: {e}")
            raise
    
    @staticmethod
    def get_audio_duration(file_path: Union[str, Path]) -> float:
        """
        Get audio duration in seconds.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Duration in seconds
        """
        waveform, sample_rate = AudioPreprocessor.load_audio(file_path)
        return len(waveform) / sample_rate
    
    @staticmethod
    def chunk_audio(
        waveform: torch.Tensor,
        sample_rate: int,
        chunk_length_s: float = 30.0,
        overlap_s: float = 5.0
    ) -> list[torch.Tensor]:
        """
        Split long audio into overlapping chunks.
        
        Args:
            waveform: Audio waveform tensor
            sample_rate: Sample rate
            chunk_length_s: Length of each chunk in seconds
            overlap_s: Overlap between chunks in seconds
            
        Returns:
            List of audio chunks
        """
        chunk_length = int(chunk_length_s * sample_rate)
        overlap = int(overlap_s * sample_rate)
        stride = chunk_length - overlap
        
        chunks = []
        start = 0
        
        while start < len(waveform):
            end = min(start + chunk_length, len(waveform))
            chunks.append(waveform[start:end])
            
            if end == len(waveform):
                break
            
            start += stride
        
        logger.info(f"Split audio into {len(chunks)} chunks")
        return chunks

    @staticmethod
    def extract_waveform_data(
        file_path: Union[str, Path],
        points_per_second: int = 50
    ) -> List[float]:
        """
        Extract waveform amplitude data for visualization.
        
        Args:
            file_path: Path to audio file
            points_per_second: Number of data points per second of audio
            
        Returns:
            Numpy array of amplitude values (0.0 to 1.0)
        """
        try:
            # Load audio (resample to lower rate for faster processing)
            # We don't need high quality for visualization
            # 4000Hz is enough to capture peaks for visual purposes
            waveform, sample_rate = AudioPreprocessor.load_audio(
                file_path, 
                target_sr=4000, 
                normalize=True
            )
            
            # Calculate chunk size for desired resolution
            chunk_size = int(sample_rate / points_per_second)
            
            # Reshape to (num_chunks, chunk_size)
            # Pad if needed
            num_samples = len(waveform)
            pad_size = chunk_size - (num_samples % chunk_size)
            if pad_size != chunk_size:
                waveform = torch.nn.functional.pad(waveform, (0, pad_size))
                
            num_chunks = len(waveform) // chunk_size
            reshaped = waveform.view(num_chunks, chunk_size)
            
            # Calculate RMS or Max amplitude for each chunk
            # Max tends to look better for waveforms than RMS
            amplitudes = torch.max(torch.abs(reshaped), dim=1)[0]
            
            # Convert to standard Python list to avoid any numpy/Qt issues
            data = amplitudes.tolist()
            logger.info(f"Waveform extracted: {len(data)} points")
            return data
            
        except Exception as e:
            logger.error(f"Failed to extract waveform data: {e}", exc_info=True)
            return []


def test_audio_utils():
    """Test audio utilities with sample file"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m src.utils.audio_utils <audio_file>")
        return
    
    audio_file = sys.argv[1]
    
    # Test validation
    is_valid = AudioPreprocessor.validate_audio_file(audio_file)
    print(f"File valid: {is_valid}")
    
    if is_valid:
        # Test loading
        waveform, sr = AudioPreprocessor.load_audio(audio_file)
        print(f"Loaded: {len(waveform)} samples at {sr}Hz")
        print(f"Duration: {len(waveform) / sr:.2f}s")
        
        # Test chunking
        chunks = AudioPreprocessor.chunk_audio(waveform, sr, chunk_length_s=10.0)
        print(f"Created {len(chunks)} chunks")


if __name__ == "__main__":
    test_audio_utils()
