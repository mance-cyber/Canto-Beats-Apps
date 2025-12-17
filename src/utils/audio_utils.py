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

# Setup FFmpeg path for packaged application
# FFmpeg is bundled with the application in the install directory
def _setup_ffmpeg_path():
    """Add FFmpeg to PATH if found in install directory (cross-platform)."""
    # Determine FFmpeg executable name based on platform
    ffmpeg_name = "ffmpeg.exe" if sys.platform == 'win32' else "ffmpeg"
    
    possible_dirs = []
    
    # Platform-specific paths
    if sys.platform == 'darwin':
        # macOS: Check Homebrew locations first
        possible_dirs.append(Path('/opt/homebrew/bin'))  # Apple Silicon
        possible_dirs.append(Path('/usr/local/bin'))      # Intel Mac
    
    # 1. Installed location: C:\Program Files\Canto-beats
    install_dir = Path(__file__).parent.parent.parent.parent
    possible_dirs.append(install_dir)
    
    # 2. Development: canto-beats root
    project_root = Path(__file__).parent.parent.parent
    possible_dirs.append(project_root)
    
    # 3. CWD
    possible_dirs.append(Path.cwd())
    
    # 4. Executable directory (for frozen apps)
    if getattr(sys, 'frozen', False):
        possible_dirs.append(Path(sys.executable).parent)
    
    for dir_path in possible_dirs:
        ffmpeg_path = dir_path / ffmpeg_name
        if ffmpeg_path.exists():
            dir_str = str(dir_path)
            # On Windows, PATH comparison is case-insensitive
            if sys.platform == 'win32':
                if dir_str.lower() not in os.environ["PATH"].lower():
                    os.environ["PATH"] = dir_str + os.pathsep + os.environ["PATH"]
                    logger.info(f"Added FFmpeg directory to PATH: {dir_str}")
            else:
                if dir_str not in os.environ["PATH"]:
                    os.environ["PATH"] = dir_str + os.pathsep + os.environ["PATH"]
                    logger.info(f"Added FFmpeg directory to PATH: {dir_str}")
            return True
    return False

_setup_ffmpeg_path()



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
        
        # Load audio using torchaudio
        waveform, sample_rate = torchaudio.load(str(file_path))
        
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
            import ffmpeg
            import subprocess
            
            # Check if ffmpeg is available (hide console window on Windows)
            import sys
            creationflags = 0
            if sys.platform == 'win32':
                creationflags = subprocess.CREATE_NO_WINDOW
            try:
                subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, creationflags=creationflags)
            except FileNotFoundError:
                error_msg = (
                    "FFmpeg executable not found in system PATH.\n"
                    "Please install FFmpeg:\n"
                    "1. Download from: https://ffmpeg.org/download.html\n"
                    "2. Add ffmpeg.exe to system PATH\n"
                    "3. Or place ffmpeg.exe in the project root directory"
                )
                logger.error(error_msg)
                raise FileNotFoundError(error_msg)
            
            # Extract audio and convert to 16kHz mono WAV
            stream = ffmpeg.input(str(video_path))
            stream = ffmpeg.output(
                stream,
                str(output_path),
                acodec='pcm_s16le',
                ac=1,  # mono
                ar=AudioPreprocessor.TARGET_SAMPLE_RATE
            )
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            
            logger.info(f"Audio extracted to: {output_path}")
            return output_path
            
        except ImportError:
            logger.error("ffmpeg-python not installed. Please install: pip install ffmpeg-python")
            raise
        except FileNotFoundError as e:
            # Re-raise with our custom message
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
