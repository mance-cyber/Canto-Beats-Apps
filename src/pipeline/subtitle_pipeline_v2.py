"""
Subtitle Pipeline V2 - AI-powered transcription with context-aware conversion.

Uses Whisper for ASR + Qwen2 LLM for intelligent colloquial-to-written conversion.
"""

import tempfile
from pathlib import Path
from typing import List, Optional, Callable
from dataclasses import dataclass

from core.config import Config
from core.hardware_detector import HardwareDetector, PerformanceProfile
from models.whisper_asr import WhisperASR
from models.qwen_llm import QwenLLM
from utils.logger import setup_logger

logger = setup_logger()


@dataclass
class SubtitleEntryV2:
    """A single subtitle entry with dual-language support."""
    start: float
    end: float
    colloquial: str  # 口語 - spoken Cantonese
    formal: Optional[str] = None  # 書面語 - written Chinese


class SubtitlePipelineV2:
    """
    V2 pipeline with AI-powered colloquial-to-written conversion.
    
    Pipeline stages:
    1. Hardware detection
    2. Model loading (Whisper ASR + optional Qwen LLM)
    3. Audio extraction (if video)
    4. Whisper transcription (native segmentation)
    5. Optional LLM refinement (context-aware conversion)
    """
    
    def __init__(self, config: Config, force_cpu: bool = False, enable_llm: bool = True):
        """
        Initialize pipeline.
        
        Args:
            config: Application configuration
            force_cpu: Force CPU mode
            enable_llm: Enable LLM refinement for better conversion
        """
        self.config = config
        self.force_cpu = force_cpu
        self.enable_llm = enable_llm
        self.profile = None
        self.asr = None
        self.llm = None
        self._models_loaded = False
        
        # Create temp directory
        self.temp_dir = Path(tempfile.gettempdir()) / "canto_beats_v2"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Initialize hardware detection
        self._setup_hardware()
    
    def _setup_hardware(self):
        """Detect hardware and determine optimal configuration."""
        logger.info("Detecting hardware configuration...")
        detector = HardwareDetector()
        self.profile = detector.detect(force_cpu=self.force_cpu)
        
        logger.info(f"Hardware tier: {self.profile.tier.value}")
        logger.info(f"Device: {self.profile.device}")
        logger.info(f"VRAM: {self.profile.vram_gb} GB")
        logger.info(f"LLM refinement: {'enabled' if self.enable_llm else 'disabled'}")
    
    def _load_asr(self, progress_callback: Optional[Callable] = None):
        """Load ASR model only (sequential loading for memory efficiency)."""
        if self.asr is not None and self.asr.is_loaded:
            return
            
        # Load ASR model with profile-selected model
        logger.info(f"Loading ASR model: {self.profile.asr_model}")
        if progress_callback:
            progress_callback(10)
            
        self.asr = WhisperASR(self.config, model_size=self.profile.asr_model)
        self.asr.load_model()
        logger.info("ASR model loaded successfully")
    
    def _unload_asr(self):
        """Unload ASR model to free GPU memory for LLM."""
        import gc
        import torch
        
        if self.asr:
            logger.info("Unloading ASR model to free GPU memory...")
            try:
                self.asr.unload_model()
            except Exception as e:
                logger.warning(f"ASR unload error: {e}")
            self.asr = None
            
            # Force garbage collection and clear GPU cache
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
            logger.info("ASR unloaded, GPU memory freed")
    
    def _load_llm(self, progress_callback: Optional[Callable] = None):
        """Load LLM model (call after ASR is unloaded for memory efficiency)."""
        if not self.enable_llm or not self.profile.llm_a_enabled:
            logger.info("LLM refinement disabled, skipping LLM load")
            return
            
        if self.llm is not None:
            return
            
        logger.info("Loading LLM for AI refinement...")
        if progress_callback:
            progress_callback(82)
        self.llm = QwenLLM(self.config, self.profile)
        self.llm.load_models()
        logger.info("LLM loaded successfully")
    
    def _extract_audio(self, video_path: Path) -> str:
        """Extract audio from video file."""
        import subprocess
        
        audio_path = self.temp_dir / f"{video_path.stem}_audio.wav"
        
        logger.info(f"Extracting audio from video: {video_path}")
        
        cmd = [
            'ffmpeg', '-y', '-i', str(video_path),
            '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
            str(audio_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {result.stderr}")
        
        logger.info(f"Audio extracted to: {audio_path}")
        return str(audio_path)
    
    def _refine_with_llm(self, segments: List, progress_callback: Optional[Callable] = None) -> List[SubtitleEntryV2]:
        """
        Refine Whisper segments using LLM for context-aware conversion.
        
        Args:
            segments: List of Whisper TranscriptionSegment objects
            progress_callback: Progress callback (80-95%)
            
        Returns:
            List of refined SubtitleEntryV2 with colloquial and formal text
        """
        if not self.llm:
            # No LLM, return segments as-is (colloquial only)
            return [
                SubtitleEntryV2(
                    start=seg.start,
                    end=seg.end,
                    colloquial=seg.text.strip(),
                    formal=None
                )
                for seg in segments
            ]
        
        logger.info(f"Refining {len(segments)} segments with LLM...")
        
        # Batch processing for efficiency
        BATCH_SIZE = 10
        refined_entries = []
        
        for i in range(0, len(segments), BATCH_SIZE):
            batch = segments[i:i + BATCH_SIZE]
            
            # Update progress
            if progress_callback:
                pct = 80 + int((i / len(segments)) * 15)
                progress_callback(pct)
            
            # Combine batch text
            batch_text = " ".join([seg.text.strip() for seg in batch])
            
            try:
                # Use LLM to refine
                result = self.llm.refine_text(batch_text)
                refined_sentences = result.get('sentences', [])
                
                # Map refined sentences back to segments
                if len(refined_sentences) == len(batch):
                    # Perfect 1:1 mapping
                    for j, seg in enumerate(batch):
                        entry = SubtitleEntryV2(
                            start=seg.start,
                            end=seg.end,
                            colloquial=seg.text.strip(),
                            formal=refined_sentences[j] if refined_sentences[j] != seg.text.strip() else None
                        )
                        refined_entries.append(entry)
                else:
                    # Fallback: use original segments
                    logger.warning(f"LLM returned {len(refined_sentences)} sentences for {len(batch)} segments, using original")
                    for seg in batch:
                        entry = SubtitleEntryV2(
                            start=seg.start,
                            end=seg.end,
                            colloquial=seg.text.strip(),
                            formal=None
                        )
                        refined_entries.append(entry)
                        
            except Exception as e:
                logger.error(f"LLM refinement error for batch {i//BATCH_SIZE}: {e}")
                # Fallback to original
                for seg in batch:
                    entry = SubtitleEntryV2(
                        start=seg.start,
                        end=seg.end,
                        colloquial=seg.text.strip(),
                        formal=None
                    )
                    refined_entries.append(entry)
        
        logger.info(f"LLM refinement complete: {len(refined_entries)} entries")
        return refined_entries
    
    def process(
        self,
        input_path: str,
        progress_callback: Optional[Callable] = None
    ) -> List[SubtitleEntryV2]:
        """
        Run the subtitle generation pipeline with sequential model loading.
        
        Pipeline stages (memory efficient - one model at a time):
        1. Load ASR (Whisper)
        2. Extract audio if needed
        3. Transcribe with Whisper
        4. Unload Whisper to free GPU memory
        5. Load LLM (if enabled)
        6. Refine with LLM
        
        Args:
            input_path: Path to audio/video file
            progress_callback: Progress callback (0-100)
            
        Returns:
            List of SubtitleEntryV2 with colloquial (and optional formal) text
        """
        logger.info(f"Starting V2 pipeline for: {input_path}")
        logger.info("Using sequential model loading (memory efficient mode)")
        input_file = Path(input_path)
        
        # Step 1: Load ASR model only (0-15%)
        self._load_asr(progress_callback)
        
        # Step 2: Prepare audio (15-20%)
        if progress_callback:
            progress_callback(15)
        
        # Check if video needs audio extraction
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.m4v'}
        if input_file.suffix.lower() in video_extensions:
            audio_path = self._extract_audio(input_file)
        else:
            audio_path = str(input_file)
        
        # Step 3: Transcribe with Whisper (20-75%)
        if progress_callback:
            progress_callback(20)
        
        logger.info("Running Whisper transcription...")
        result = self.asr.transcribe(audio_path, language='yue')
        
        whisper_segments = result.get('segments', [])
        logger.info(f"Whisper produced {len(whisper_segments)} segments")
        
        if not whisper_segments:
            logger.warning("No segments from Whisper")
            return []
        
        if progress_callback:
            progress_callback(75)
        
        # Step 4: Unload Whisper to free GPU memory (75-80%)
        if self.enable_llm and self.profile.llm_a_enabled:
            self._unload_asr()
            if progress_callback:
                progress_callback(80)
        
        # Step 5: LLM refinement (80-95%)
        if self.enable_llm:
            # Load LLM now that Whisper is unloaded
            self._load_llm(progress_callback)
            
            logger.info("Starting LLM refinement...")
            final_subtitles = self._refine_with_llm(whisper_segments, progress_callback)
        else:
            # No LLM, convert segments directly
            final_subtitles = [
                SubtitleEntryV2(
                    start=seg.start,
                    end=seg.end,
                    colloquial=seg.text.strip(),
                    formal=None
                )
                for seg in whisper_segments
            ]
        
        if progress_callback:
            progress_callback(100)
        
        logger.info(f"Pipeline complete. Generated {len(final_subtitles)} subtitles")
        return final_subtitles
    
    def cleanup(self):
        """Release all resources."""
        import gc
        import torch
        
        logger.info("Cleaning up pipeline resources...")
        
        if self.asr:
            try:
                self.asr.unload_model()
            except Exception as e:
                logger.warning(f"ASR cleanup error: {e}")
            self.asr = None
        
        if self.llm:
            try:
                self.llm.unload_models()
            except Exception as e:
                logger.warning(f"LLM cleanup error: {e}")
            self.llm = None
        
        self._models_loaded = False
        
        # Force garbage collection
        gc.collect()
        
        # Clear GPU memory cache (safe to call from main thread)
        if torch.cuda.is_available():
            try:
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
                logger.info("GPU memory cache cleared")
            except Exception as e:
                logger.warning(f"GPU cache clear error: {e}")
        
        logger.info("Pipeline cleanup complete")
    
    def get_profile(self) -> Optional[PerformanceProfile]:
        """Get the current hardware profile."""
        return self.profile
