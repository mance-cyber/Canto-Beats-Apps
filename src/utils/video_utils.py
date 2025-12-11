"""
Video utilities for thumbnail extraction with caching support.
"""

import os
import tempfile
import subprocess
import hashlib
import json
import shutil
from pathlib import Path
from typing import List, Tuple, Optional
import ffmpeg
from utils.logger import setup_logger

logger = setup_logger()

# Cache directory
CACHE_DIR = Path.home() / ".canto-beats" / "thumbnail_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class VideoThumbnailExtractor:
    """
    Extract video thumbnails using FFmpeg with GPU acceleration support.
    """
    
    _gpu_available = None  # Cache GPU availability check
    
    @classmethod
    def _check_gpu_availability(cls) -> bool:
        """
        Check if GPU (CUDA) is available for video processing.
        
        Returns:
            True if GPU is available, False otherwise
        """
        if cls._gpu_available is not None:
            return cls._gpu_available
        
        # Method 1: Check if PyTorch reports CUDA availability
        try:
            import torch
            if torch.cuda.is_available():
                logger.info(f"GPU detected via PyTorch: {torch.cuda.get_device_name(0)}")
                cls._gpu_available = True
                return True
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"PyTorch CUDA check failed: {e}")
        
        # Method 2: Check if FFmpeg supports CUDA
        try:
            result = subprocess.run(
                ['ffmpeg', '-hwaccels'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if 'cuda' in result.stdout.lower():
                logger.info("GPU detected via FFmpeg hwaccel list")
                cls._gpu_available = True
                return True
        except Exception as e:
            logger.debug(f"FFmpeg CUDA check failed: {e}")
        
        logger.info("No GPU detected, will use CPU for thumbnail extraction")
        cls._gpu_available = False
        return False
    
    @staticmethod
    def extract_thumbnails(
        video_path: str,
        interval: int = 5,
        max_width: int = 160,
        max_height: int = 90,
        use_gpu: Optional[bool] = None,
        use_cache: bool = True
    ) -> List[Tuple[float, str]]:
        """
        Extract video thumbnails at regular intervals with caching support.
        
        Args:
            video_path: Path to video file
            interval: Interval in seconds between thumbnails
            max_width: Maximum thumbnail width
            max_height: Maximum thumbnail height
            use_gpu: Use GPU acceleration. If None, auto-detect.
            use_cache: Use cached thumbnails if available
            
        Returns:
            List of (timestamp, image_path) tuples
        """
        try:
            video_path = Path(video_path)
            if not video_path.exists():
                logger.error(f"Video file not found: {video_path}")
                return []
            
            # Generate cache key based on file path, size, and mtime
            file_stat = video_path.stat()
            cache_key = hashlib.md5(
                f"{video_path.absolute()}_{file_stat.st_size}_{file_stat.st_mtime}_{interval}".encode()
            ).hexdigest()
            cache_subdir = CACHE_DIR / cache_key
            cache_meta_file = cache_subdir / "meta.json"
            
            # Try to load from cache
            if use_cache and cache_meta_file.exists():
                try:
                    with open(cache_meta_file, 'r') as f:
                        meta = json.load(f)
                    
                    # Verify all thumbnail files exist
                    cached_thumbs = []
                    all_exist = True
                    for timestamp, rel_path in meta['thumbnails']:
                        abs_path = cache_subdir / rel_path
                        if abs_path.exists():
                            cached_thumbs.append((timestamp, str(abs_path)))
                        else:
                            all_exist = False
                            break
                    
                    if all_exist:
                        logger.info(f"✨ Loaded {len(cached_thumbs)} thumbnails from cache (instant!)")
                        return cached_thumbs
                except Exception as e:
                    logger.debug(f"Cache load failed: {e}")
            
            # Auto-detect GPU if not specified
            if use_gpu is None:
                use_gpu = VideoThumbnailExtractor._check_gpu_availability()
            
            # Get video duration
            probe = ffmpeg.probe(str(video_path))
            duration = float(probe['format']['duration'])
            
            logger.info(f"Extracting thumbnails from {video_path.name}, duration: {duration:.1f}s, GPU: {use_gpu}")
            
            # Create cache directory for this video
            cache_subdir.mkdir(parents=True, exist_ok=True)
            
            thumbnails = []
            gpu_failed = False
            
            # Extract thumbnails at intervals
            current_time = 0
            frame_count = 0
            
            while current_time < duration:
                output_filename = f"thumb_{frame_count:04d}.jpg"
                output_path = cache_subdir / output_filename
                
                try:
                    # GPU priority: Try CUDA hardware acceleration first
                    safe_width = (max_width // 2) * 2
                    safe_height = (max_height // 2) * 2
                    
                    if use_gpu and not gpu_failed:
                        try:
                            # CUDA GPU decoding
                            input_kwargs = {
                                'ss': current_time,
                                'hwaccel': 'cuda',
                                'hwaccel_device': '0',
                            }
                            
                            (
                                ffmpeg
                                .input(str(video_path), **input_kwargs)
                                .filter('scale', safe_width, safe_height, 
                                       force_original_aspect_ratio='decrease')
                                .filter('format', 'yuv420p')  # Proper color format
                                .output(str(output_path), vframes=1, format='image2', 
                                       vcodec='mjpeg', qscale=2)
                                .overwrite_output()
                                .run(capture_stdout=True, capture_stderr=True, quiet=True)
                            )
                        except ffmpeg.Error as e:
                            logger.warning(f"GPU thumbnail failed, falling back to CPU")
                            gpu_failed = True
                            # Fall through to CPU extraction
                    
                    # CPU fallback or if GPU failed
                    if not use_gpu or gpu_failed:
                        (
                            ffmpeg
                            .input(str(video_path), ss=current_time)
                            .filter('scale', safe_width, safe_height, 
                                   force_original_aspect_ratio='decrease')
                            .filter('format', 'yuv420p')
                            .output(str(output_path), vframes=1, format='image2', 
                                   vcodec='mjpeg', qscale=2)
                            .overwrite_output()
                            .run(capture_stdout=True, capture_stderr=True, quiet=True)
                        )
                    
                    if output_path.exists():
                        thumbnails.append((current_time, str(output_path)))
                        if frame_count == 0:
                            logger.debug(f"First thumbnail extracted at {current_time}s using {'GPU' if use_gpu and not gpu_failed else 'CPU'}")
                    
                except ffmpeg.Error as e:
                    logger.warning(f"Failed to extract thumbnail at {current_time}s: {e.stderr.decode() if e.stderr else str(e)}")
                
                current_time += interval
                frame_count += 1
            
            # Save cache metadata
            if use_cache and thumbnails:
                try:
                    meta = {
                        'video_path': str(video_path.absolute()),
                        'file_size': file_stat.st_size,
                        'mtime': file_stat.st_mtime,
                        'interval': interval,
                        'thumbnails': [(ts, Path(p).name) for ts, p in thumbnails]
                    }
                    with open(cache_meta_file, 'w') as f:
                        json.dump(meta, f)
                    logger.debug(f"Saved {len(thumbnails)} thumbnails to cache")
                except Exception as e:
                    logger.warning(f"Failed to save cache: {e}")
            
            logger.info(f"Extracted {len(thumbnails)} thumbnails using {'GPU' if not gpu_failed else 'CPU'}")
            return thumbnails
                
        except Exception as e:
            logger.error(f"Thumbnail extraction failed: {e}", exc_info=True)
            return []

    
    @staticmethod
    def cleanup_thumbnails(thumbnail_paths: List[Tuple[float, str]]):
        """
        Clean up temporary thumbnail files.
        
        Args:
            thumbnail_paths: List of (timestamp, image_path) tuples
        """
        try:
            if not thumbnail_paths:
                return
                
            # Get temp directory from first thumbnail
            first_path = Path(thumbnail_paths[0][1])
            temp_dir = first_path.parent
            
            # Remove all files in temp directory
            for _, path in thumbnail_paths:
                try:
                    Path(path).unlink(missing_ok=True)
                except Exception as e:
                    logger.warning(f"Failed to delete thumbnail {path}: {e}")
            
            # Remove temp directory
            try:
                temp_dir.rmdir()
            except Exception as e:
                logger.warning(f"Failed to remove temp directory {temp_dir}: {e}")
                
        except Exception as e:
            logger.error(f"Thumbnail cleanup failed: {e}")
