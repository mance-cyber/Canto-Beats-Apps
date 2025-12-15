"""
Silero VAD (Voice Activity Detection) processor.

Provides intelligent sentence segmentation for Cantonese speech.
"""

import os
import torch
import numpy as np
from pathlib import Path
from typing import List, Dict, Union, Tuple, Optional
from dataclasses import dataclass

from models.model_manager import ModelManager
from models.whisper_asr import TranscriptionSegment
from core.config import Config
from utils.logger import setup_logger
from utils.audio_utils import AudioPreprocessor


logger = setup_logger()


@dataclass
class VoiceSegment:
    """A segment of detected voice activity."""
    
    start: float  # Start time in seconds
    end: float    # End time in seconds
    confidence: float


class VADProcessor(ModelManager):
    """
    Silero VAD for voice activity detection and sentence segmentation.
    
    Provides:
    - Voice activity detection
    - Silence removal
    - Smart sentence boundary detection
    - Integration with Whisper transcription timestamps
    """
    
    def __init__(
        self,
        config: Config,
        threshold: float = 0.5,
        min_silence_duration_ms: int = 200,
        min_speech_duration_ms: int = 250,
        speech_pad_ms: int = 400
    ):
        """
        Initialize VAD processor.
        
        Args:
            config: Application configuration
            threshold: Voice detection threshold (0.0-1.0)
            min_silence_duration_ms: Minimum silence duration to split sentences
            min_speech_duration_ms: Minimum speech duration to consider
            speech_pad_ms: Padding around speech segments (ms)
        """
        super().__init__(config)
        
        self.threshold = threshold
        self.min_silence_duration_ms = min_silence_duration_ms
        self.min_speech_duration_ms = min_speech_duration_ms
        self.speech_pad_ms = speech_pad_ms
        self.audio_preprocessor = AudioPreprocessor()
        
        logger.info(f"VAD processor initialized (threshold={threshold})")
    
    def load_model(self):
        """Load Silero VAD model."""
        if self.is_loaded:
            logger.warning("VAD model already loaded")
            return
        
        logger.info("Loading Silero VAD model")
        
        try:
            # Download Silero VAD model from torch hub
            self.model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                onnx=False,
                trust_repo=True  # Required for newer PyTorch versions
            )
            
            # Extract utility functions
            (self.get_speech_timestamps,
             self.save_audio,
             self.read_audio,
             self.VADIterator,
             self.collect_chunks) = utils
            
            # Override read_audio to use soundfile instead of torchaudio
            # This avoids torchcodec dependency issues on Windows Standalone
            self.read_audio = self._read_audio_soundfile
            
            # Move model to device
            self.model = self.model.to(self.device)
            self.is_loaded = True
            
            logger.info(f"Silero VAD model loaded on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to load VAD model: {e}")
            raise
    
    def _read_audio_soundfile(self, path: str, sampling_rate: int = 16000):
        """
        Read audio using soundfile instead of torchaudio.
        This is a drop-in replacement for Silero's read_audio utility.
        
        Args:
            path: Path to audio file
            sampling_rate: Target sampling rate (default 16000 for VAD)
            
        Returns:
            torch.Tensor of audio samples
        """
        try:
            import soundfile as sf
            import librosa
            
            # Read audio file
            audio, sr = sf.read(path)
            
            # Convert to mono if stereo
            if len(audio.shape) > 1:
                audio = audio.mean(axis=1)
            
            # Resample if needed
            if sr != sampling_rate:
                audio = librosa.resample(audio, orig_sr=sr, target_sr=sampling_rate)
            
            # Convert to torch tensor (float32)
            wav = torch.from_numpy(audio).float()
            
            return wav
            
        except Exception as e:
            logger.error(f"Failed to read audio with soundfile: {e}")
            raise
    
    def unload_model(self):
        """Unload VAD model and free memory."""
        if not self.is_loaded:
            return
        
        logger.info("Unloading VAD model")
        
        del self.model
        self.model = None
        self.is_loaded = False
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    def detect_voice_segments(
        self,
        audio_path: Union[str, Path],
        return_seconds: bool = True
    ) -> List[VoiceSegment]:
        """
        Detect voice activity segments in audio.
        
        Args:
            audio_path: Path to audio file
            return_seconds: Return timestamps in seconds (vs samples)
            
        Returns:
            List of VoiceSegment objects
        """
        if not self.is_loaded:
            self.load_model()
        
        logger.info(f"Detecting voice segments: {audio_path}")
        
        # Read audio using Silero's utility
        wav = self.read_audio(str(audio_path), sampling_rate=16000)
        
        # CRITICAL: Move audio tensor to same device as model
        wav = wav.to(self.device)
        
        # Get speech timestamps
        speech_timestamps = self.get_speech_timestamps(
            wav,
            self.model,
            threshold=self.threshold,
            sampling_rate=16000,
            min_speech_duration_ms=self.min_speech_duration_ms,
            min_silence_duration_ms=self.min_silence_duration_ms,
            speech_pad_ms=self.speech_pad_ms,
            return_seconds=return_seconds
        )
        
        # Convert to VoiceSegment objects
        segments = []
        for ts in speech_timestamps:
            segment = VoiceSegment(
                start=ts['start'],
                end=ts['end'],
                confidence=1.0  # Silero doesn't provide confidence
            )
            segments.append(segment)
        
        logger.info(f"Detected {len(segments)} voice segments")
        
        return segments
    
    def merge_with_transcription(
        self,
        transcription_segments: List[TranscriptionSegment],
        voice_segments: List[VoiceSegment],
        max_gap: float = 1.0,
        max_chars: int = 30
    ) -> List[TranscriptionSegment]:
        """
        Merge VAD voice segments with Whisper transcription segments.
        
        Args:
            transcription_segments: Whisper transcription segments
            voice_segments: VAD voice activity segments
            max_gap: Maximum gap (seconds) to merge segments
            max_chars: Maximum characters per segment
            
        Returns:
            Merged and optimized transcription segments
        """
        logger.info(f"Merging {len(transcription_segments)} transcription segments with {len(voice_segments)} VAD segments")
        
        # 1. Align with VAD
        aligned_segments = []
        for trans_seg in transcription_segments:
            # Find overlapping voice segments
            overlapping_voice = []
            for voice_seg in voice_segments:
                if self._segments_overlap(
                    (trans_seg.start, trans_seg.end),
                    (voice_seg.start, voice_seg.end)
                ):
                    overlapping_voice.append(voice_seg)
            
            if overlapping_voice:
                vad_start = min(v.start for v in overlapping_voice)
                vad_end = max(v.end for v in overlapping_voice)
                
                adjusted_seg = TranscriptionSegment(
                    id=trans_seg.id,
                    start=max(trans_seg.start, vad_start),
                    end=min(trans_seg.end, vad_end),
                    text=trans_seg.text,
                    confidence=trans_seg.confidence,
                    language=trans_seg.language,
                    words=trans_seg.words
                )
                
                # Filter out tiny segments (likely noise)
                if adjusted_seg.end - adjusted_seg.start >= 0.2:
                    aligned_segments.append(adjusted_seg)
            else:
                # No VAD overlap = Noise/Hallucination in silence
                # We trust VAD logic: if it says silence, we drop the transcription
                logger.debug(f"Dropped segment (no VAD): {trans_seg.text} [{trans_seg.start}-{trans_seg.end}]")
                continue
        
        # 2. Split long segments
        split_segments = []
        for seg in aligned_segments:
            if len(seg.text) > max_chars:
                split_segments.extend(self._split_long_segment(seg, max_chars))
            else:
                split_segments.append(seg)
                
        # 3. Merge close segments (respecting max_chars)
        final_segments = self._merge_close_segments(split_segments, max_gap, max_chars)
        
        logger.info(f"Created {len(final_segments)} final segments")
        return final_segments

    def _segments_overlap(
        self,
        seg1: Tuple[float, float],
        seg2: Tuple[float, float]
    ) -> bool:
        """
        Check if two time segments overlap.
        
        Args:
            seg1: (start, end) tuple
            seg2: (start, end) tuple
            
        Returns:
            True if segments overlap
        """
        return seg1[0] <= seg2[1] and seg2[0] <= seg1[1]

    def _split_long_segment(
        self, 
        segment: TranscriptionSegment, 
        max_chars: int
    ) -> List[TranscriptionSegment]:
        """
        Split a long segment into smaller chunks using natural boundaries.
        
        Priorities:
        1. Punctuation (，。！？、)
        2. Silence gaps (> 0.2s)
        3. Balanced length
        """
        if len(segment.text) <= max_chars:
            return [segment]
            
        if not segment.words:
            # Fallback for no word timestamps: simple length split
            return self._split_by_length(segment, max_chars)
            
        chunks = []
        words = segment.words
        n_words = len(words)
        
        start_idx = 0
        
        while start_idx < n_words:
            # 1. Determine maximum possible reach
            current_chars = 0
            end_idx = start_idx
            
            # Look ahead to find how many words fit in max_chars
            while end_idx < n_words:
                word_len = len(words[end_idx].get('word', '').strip())
                if current_chars + word_len > max_chars and end_idx > start_idx:
                    break
                current_chars += word_len
                end_idx += 1
            
            # If we reached the end, just take it
            if end_idx == n_words:
                chunks.append(self._create_segment_from_words(
                    segment, words[start_idx:end_idx]
                ))
                break
                
            # 2. Find best split point in range [start_idx, end_idx]
            # We look for the "best" split point working backwards from end_idx
            # to maximize line usage while respecting natural boundaries.
            
            best_split = -1
            best_score = -1
            
            # Only consider splitting if we have enough content (e.g. at least 1/3 filled)
            min_split_idx = start_idx + max(1, (end_idx - start_idx) // 3)
            
            for i in range(end_idx - 1, min_split_idx - 1, -1):
                # Ensure we don't go out of bounds when accessing next word
                if i + 1 >= n_words:
                    continue
                    
                curr_word = words[i]
                next_word = words[i+1]
                
                score = 0
                
                # Factor 1: Punctuation (Highest priority)
                text = curr_word.get('word', '').strip()
                if any(p in text for p in '，。！？、；,.;?!'):
                    score += 100
                
                # Factor 1.5: Cantonese Sentence-Final Particles (New)
                # Common particles: 囉, 喎, 㗎, 呢, 嘅, 呀, 嘛, 啦, 咋, 啩
                particles = {'囉', '喎', '㗎', '呢', '嘅', '呀', '嘛', '啦', '咋', '啩', '咯', '咩'}
                if any(p in text for p in particles):
                    # Only boost if it's at the end of the word or is the word itself
                    if text[-1] in particles:
                        score += 80
                
                # Factor 2: Silence Gap
                gap = next_word['start'] - curr_word['end']
                if gap > 0.1:  # Lowered to 100ms for particles
                    # Boost gap score if preceded by a particle
                    if any(p in text for p in particles):
                        score += min(gap * 200, 100) # Strong boost for particle + gap
                    else:
                        score += 50 + min(gap * 10, 20)
                
                # Factor 3: Balance (Prefer splitting near the middle/end)
                # We prefer filling the line, so closer to end_idx is better
                # But we also don't want to leave a tiny orphan on the next line
                dist_from_max = end_idx - i
                score -= dist_from_max * 2  # Penalty for being too far from max
                
                if score > best_score:
                    best_score = score
                    best_split = i + 1  # Split AFTER this word
            
            # If no good split found, just split at max length (end_idx)
            if best_split == -1:
                best_split = end_idx
                
            # Create chunk
            chunks.append(self._create_segment_from_words(
                segment, words[start_idx:best_split]
            ))
            
            start_idx = best_split
            
        return chunks

    def _create_segment_from_words(self, original_seg, words_subset):
        """Helper to create a segment from a subset of words."""
        if not words_subset:
            return None
            
        start = words_subset[0]['start']
        end = words_subset[-1]['end']
        text = "".join(w['word'] for w in words_subset).strip()
        
        return TranscriptionSegment(
            id=0,  # Will be re-indexed later
            start=start,
            end=end,
            text=text,
            confidence=original_seg.confidence,
            language=original_seg.language,
            words=words_subset
        )

    def _split_by_length(self, segment, max_chars):
        """Fallback splitting when no word timestamps available."""
        text = segment.text
        if len(text) <= max_chars:
            return [segment]
            
        chunks = []
        duration = segment.end - segment.start
        chars_per_sec = len(text) / duration if duration > 0 else 0
        
        for i in range(0, len(text), max_chars):
            chunk_text = text[i:i+max_chars]
            chunk_len = len(chunk_text)
            
            # Estimate timing
            chunk_duration = chunk_len / chars_per_sec if chars_per_sec > 0 else 0
            chunk_start = segment.start + (i / len(text)) * duration
            chunk_end = min(segment.end, chunk_start + chunk_duration)
            
            chunks.append(TranscriptionSegment(
                id=0,
                start=chunk_start,
                end=chunk_end,
                text=chunk_text,
                confidence=segment.confidence,
                language=segment.language
            ))
            
        return chunks

    def _merge_close_segments(
        self,
        segments: List[TranscriptionSegment],
        max_gap: float,
        max_chars: int
    ) -> List[TranscriptionSegment]:
        """Merge segments that are close together."""
        if not segments:
            return []
        
        merged = []
        current = segments[0]
        
        for next_seg in segments[1:]:
            gap = next_seg.start - current.end
            combined_len = len(current.text) + len(next_seg.text)
            
            if gap <= max_gap and combined_len <= max_chars:
                # Merge
                current = TranscriptionSegment(
                    id=current.id,
                    start=current.start,
                    end=next_seg.end,
                    text=current.text + " " + next_seg.text,
                    confidence=min(current.confidence, next_seg.confidence),
                    language=current.language,
                    words=(current.words or []) + (next_seg.words or [])
                )
            else:
                merged.append(current)
                current = next_seg
        
        merged.append(current)
        return merged

    def remove_silence(
        self,
        audio_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None
    ) -> Path:
        """
        Remove silence from audio file.
        
        Args:
            audio_path: Input audio file
            output_path: Output audio file (optional)
            
        Returns:
            Path to processed audio file
        """
        if not self.is_loaded:
            self.load_model()
        
        logger.info(f"Removing silence from: {audio_path}")
        
        # Detect voice segments
        voice_segments = self.detect_voice_segments(audio_path, return_seconds=False)
        
        # Read audio
        wav = self.read_audio(str(audio_path), sampling_rate=16000)
        
        # Move to same device as model
        wav = wav.to(self.device)
        
        # Collect voice chunks
        timestamps = [{'start': int(v.start), 'end': int(v.end)} for v in voice_segments]
        speech_audio = self.collect_chunks(timestamps, wav)
        
        # Save
        if output_path is None:
            output_path = Path(audio_path).with_suffix('.denoised.wav')
        else:
            output_path = Path(output_path)
        
        self.save_audio(str(output_path), speech_audio, sampling_rate=16000)
        
        logger.info(f"Silence removed, saved to: {output_path}")
        
        return output_path
    
    def remove_silence(
        self,
        audio_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None
    ) -> Path:
        """
        Remove silence from audio file.
        
        Args:
            audio_path: Input audio file
            output_path: Output audio file (optional)
            
        Returns:
            Path to processed audio file
        """
        if not self.is_loaded:
            self.load_model()
        
        logger.info(f"Removing silence from: {audio_path}")
        
        # Detect voice segments
        voice_segments = self.detect_voice_segments(audio_path, return_seconds=False)
        
        # Read audio
        wav = self.read_audio(str(audio_path), sampling_rate=16000)
        
        # Move to same device as model
        wav = wav.to(self.device)
        
        # Collect voice chunks
        timestamps = [{'start': int(v.start), 'end': int(v.end)} for v in voice_segments]
        speech_audio = self.collect_chunks(timestamps, wav)
        
        # Save
        if output_path is None:
            output_path = Path(audio_path).with_suffix('.denoised.wav')
        else:
            output_path = Path(output_path)
        
        self.save_audio(str(output_path), speech_audio, sampling_rate=16000)
        
        logger.info(f"Silence removed, saved to: {output_path}")
        
        return output_path
    
    def get_speech_ratio(self, audio_path: Union[str, Path]) -> float:
        """
        Calculate the ratio of speech to total audio duration.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Speech ratio (0.0-1.0)
        """
        voice_segments = self.detect_voice_segments(audio_path)
        
        total_speech = sum(seg.end - seg.start for seg in voice_segments)
        total_duration = self.audio_preprocessor.get_audio_duration(audio_path)
        
        ratio = total_speech / total_duration if total_duration > 0 else 0.0
        
        logger.info(f"Speech ratio: {ratio:.2%} ({total_speech:.1f}s / {total_duration:.1f}s)")
        
        return ratio


def test_vad():
    """Test VAD processor with sample audio file."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m src.models.vad_processor <audio_file>")
        return
    
    audio_file = sys.argv[1]
    
    # Initialize
    from core.config import Config
    config = Config()
    
    vad = VADProcessor(config, threshold=0.5)
    
    # Load model
    print("Loading VAD model...")
    vad.load_model()
    
    # Detect voice segments
    print("\nDetecting voice segments...")
    segments = vad.detect_voice_segments(audio_file)
    
    print(f"\nFound {len(segments)} voice segments:")
    for i, seg in enumerate(segments[:10]):  # Show first 10
        print(f"  {i+1}. [{seg.start:.2f}s - {seg.end:.2f}s] ({seg.end - seg.start:.2f}s)")
    
    # Get speech ratio
    ratio = vad.get_speech_ratio(audio_file)
    print(f"\nSpeech ratio: {ratio:.2%}")
    
    # Cleanup
    vad.cleanup()
    print("\nDone!")


if __name__ == "__main__":
    test_vad()
