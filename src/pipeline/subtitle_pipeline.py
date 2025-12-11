"""
Subtitle Generation Pipeline.
Integrates VAD, Whisper ASR, and LLM for high-quality Cantonese subtitles.
"""

import os
import torch
import logging
import tempfile
import torchaudio
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from core.config import Config
from models.vad_processor import VADProcessor, VoiceSegment
from models.whisper_asr import WhisperASR, TranscriptionSegment
from models.llm_processor import LLMProcessor
from utils.audio_utils import AudioPreprocessor
from utils.logger import setup_logger

logger = setup_logger()

@dataclass
class SubtitleEntry:
    """Final subtitle entry."""
    start: float
    end: float
    text: str

class SubtitlePipeline:
    """
    Orchestrates the VAD -> Batching -> Usage -> LLM pipeline.
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.temp_dir = Path(tempfile.gettempdir()) / "canto_beats_pipeline"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.vad = VADProcessor(
            config, 
            threshold=config.get('vad_threshold', 0.5),
            min_silence_duration_ms=config.get('min_silence_duration_ms', 400), # Sensitive
            min_speech_duration_ms=config.get('min_speech_duration_ms', 200),
            speech_pad_ms=config.get('vad_speech_pad_ms', 200)
        )
        
        self.asr = WhisperASR(config)
        self.llm = LLMProcessor(config)
        self.audio_preprocessor = AudioPreprocessor()
        
    def process(self, audio_path: str, progress_callback=None) -> List[SubtitleEntry]:
        """
        Run the full subtitle generation pipeline.
        
        Args:
            audio_path: Path to the input audio file.
            progress_callback: Optional callback for progress updates (0-100).
            
        Returns:
            List of SubtitleEntry objects.
        """
        logger.info(f"Starting pipeline processing for: {audio_path}")
        
        if progress_callback: progress_callback(5)
        
        # 1. Prepare Audio (Extract from video if needed)
        input_path = Path(audio_path)
        process_audio_path = input_path
        extracted_audio = False
        
        video_extensions = {'.mp4', '.mkv', '.mov', '.avi', '.rmvb', '.ts', '.flv', '.webm', '.mpg', '.wmv'}
        
        if input_path.suffix.lower() in video_extensions:
            logger.info("Input appears to be video, extracting audio for processing...")
            extracted_audio_path = self.temp_dir / f"{input_path.stem}_extracted.wav"
            try:
                process_audio_path = self.audio_preprocessor.extract_audio_from_video(
                    input_path, 
                    output_path=extracted_audio_path
                )
                extracted_audio = True
            except Exception as e:
                logger.error(f"Failed to extract audio from video: {e}")
                # Fallback to trying to read directly
                pass
        
        
        # 1b. Load Audio Waveform
        waveform, sr = self.audio_preprocessor.load_audio(process_audio_path, normalize=True)
            
        # 2. VAD Segmentation
        logger.info(f"Running VAD on: {process_audio_path}")
        voice_segments = self.vad.detect_voice_segments(process_audio_path)

        
        if not voice_segments:
            logger.warning("No voice segments detected.")
            return []
            
        if progress_callback: progress_callback(15)
        
        # 3. Batching (3 segments per batch)
        BATCH_SIZE = 3
        batches = []
        current_batch = []
        
        for seg in voice_segments:
            current_batch.append(seg)
            if len(current_batch) >= BATCH_SIZE:
                batches.append(current_batch)
                current_batch = []
        
        if current_batch:
            batches.append(current_batch)
            
        logger.info(f"Created {len(batches)} batches from {len(voice_segments)} segments")
        
        # 4. Processing Batches
        final_subtitles = []
        total_batches = len(batches)
        
        # Reuse temp file for batch audio
        batch_audio_path = self.temp_dir / "batch_temp.wav"
        
        for i, batch in enumerate(batches):
            try:
                # Calculate progress
                if progress_callback:
                    current_progress = 15 + int((i / total_batches) * 80)
                    progress_callback(current_progress)
                
                # Determine batch time range
                batch_start = batch[0].start
                batch_end = batch[-1].end
                
                # Extract audio for this batch
                start_sample = int(batch_start * sr)
                end_sample = int(batch_end * sr)
                
                # Ensure we don't go out of bounds
                end_sample = min(end_sample, waveform.shape[0])
                if start_sample >= end_sample:
                    continue
                    
                batch_waveform = waveform[start_sample:end_sample]
                
                # Save batch audio to temp file (Whisper needs file path)
                torchaudio.save(
                    str(batch_audio_path), 
                    batch_waveform.unsqueeze(0), 
                    sr
                )
                
                # ASR
                # We use specific prompts for Cantonese if needed, but config default is usually good
                asr_result = self.asr.transcribe(str(batch_audio_path))
                raw_text = asr_result.get('text', '').strip()
                
                if not raw_text:
                    continue
                    
                logger.debug(f"Batch {i+1} Raw ASR: {raw_text}")
                
                # LLM Processing
                refined_sentences = self.llm.refine_text(raw_text)
                
                logger.debug(f"Batch {i+1} LLM Refined: {refined_sentences}")
                
                # Create Subtitle Entries with Smart Mapping
                # Strategy: 
                # 1. If LLM returns same # of sentences as batch size -> Map 1:1 to VAD segments
                # 2. If mismatch -> Distribute linearly across the total batch duration (Fallback)
                
                num_vad = len(batch)
                num_llm = len(refined_sentences)
                
                if num_vad == num_llm:
                    # Perfect match - ideal scenario
                    for j, sent in enumerate(refined_sentences):
                        seg = batch[j]
                        entry = SubtitleEntry(
                            start=seg.start,
                            end=seg.end,
                            text=sent
                        )
                        final_subtitles.append(entry)
                else:
                    # Mismatch (LLM merged or split sentences)
                    # We map the new sentences into the total time range of the batch
                    logger.info(f"Batch {i+1} mismatch: {num_vad} VAD segments vs {num_llm} LLM sentences. Remapping times.")
                    
                    total_chars = sum(len(s) for s in refined_sentences)
                    if total_chars == 0: total_chars = 1
                    
                    current_time = batch_start
                    total_duration = batch_end - batch_start
                    
                    for sent in refined_sentences:
                        # Proportional duration based on length
                        ratio = len(sent) / total_chars
                        duration = total_duration * ratio
                        
                        entry = SubtitleEntry(
                            start=current_time,
                            end=current_time + duration,
                            text=sent
                        )
                        final_subtitles.append(entry)
                        current_time += duration
                
            except Exception as e:
                logger.error(f"Error processing batch {i+1}: {e}")
                continue
                
        if progress_callback: progress_callback(100)
        logger.info("Pipeline processing complete")
        return final_subtitles

    def cleanup(self):
        """Cleanup resources."""
        if hasattr(self, 'vad'): self.vad.unload_model()
        if hasattr(self, 'asr'): self.asr.unload_model()
        # LLM doesn't need unloading (HTTP)
