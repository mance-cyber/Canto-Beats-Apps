"""
AVFoundation-based video thumbnail extraction for Apple Silicon.

Uses native macOS APIs for hardware-accelerated thumbnail generation.
Much faster than FFmpeg on Apple Silicon Macs.
"""

import sys
import os
from pathlib import Path
from typing import List, Tuple, Optional
import hashlib
import json

from utils.logger import setup_logger

logger = setup_logger()

# Cache directory
CACHE_DIR = Path.home() / ".canto-beats" / "thumbnail_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class AVFoundationThumbnailExtractor:
    """
    Extract video thumbnails using Apple's AVFoundation framework.
    
    This is significantly faster than FFmpeg on Apple Silicon because it uses
    native hardware video decoding via VideoToolbox.
    """
    
    _avfoundation_available = None
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if AVFoundation is available (macOS only)."""
        if cls._avfoundation_available is not None:
            return cls._avfoundation_available

        if sys.platform != 'darwin':
            cls._avfoundation_available = False
            return False

        try:
            # Test actual import
            from AVFoundation import AVURLAsset, AVAssetImageGenerator
            from Foundation import NSURL
            from CoreMedia import CMTimeMake
            from Quartz import CGImageDestinationCreateWithURL, CGSizeMake

            cls._avfoundation_available = True
            logger.info("AVFoundation available for native thumbnail extraction")
            return True
        except ImportError as e:
            cls._avfoundation_available = False
            logger.debug(f"AVFoundation not available: {e}")
            return False
        except Exception as e:
            cls._avfoundation_available = False
            logger.debug(f"AVFoundation check failed: {e}")
            return False
    
    @staticmethod
    def extract_thumbnails(
        video_path: str,
        interval: int = 5,
        max_width: int = 160,
        max_height: int = 90,
        use_cache: bool = True
    ) -> List[Tuple[float, str]]:
        """
        Extract video thumbnails using AVFoundation.
        
        Args:
            video_path: Path to video file
            interval: Interval in seconds between thumbnails
            max_width: Maximum thumbnail width
            max_height: Maximum thumbnail height
            use_cache: Use cached thumbnails if available
            
        Returns:
            List of (timestamp, image_path) tuples
        """
        try:
            import objc
            from Foundation import NSURL
            from AVFoundation import AVURLAsset, AVAssetImageGenerator
            from CoreMedia import CMTimeMake, CMTimeGetSeconds
            from Quartz import (
                CGImageDestinationCreateWithURL,
                CGImageDestinationAddImage,
                CGImageDestinationFinalize,
                kCGImageDestinationLossyCompressionQuality,
                CGSizeMake  # CoreGraphics is part of Quartz
            )
            from UniformTypeIdentifiers import UTTypeJPEG
            
            video_path = Path(video_path)
            if not video_path.exists():
                logger.error(f"Video file not found: {video_path}")
                return []
            
            # Generate cache key
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
                        logger.info(f"⚡ Loaded {len(cached_thumbs)} thumbnails from cache (instant!)")
                        return cached_thumbs
                except Exception as e:
                    logger.debug(f"Cache load failed: {e}")
            
            # Create cache directory
            cache_subdir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"🍎 Extracting thumbnails using AVFoundation: {video_path.name}")
            
            # Create AVAsset from video URL
            video_url = NSURL.fileURLWithPath_(str(video_path.absolute()))
            asset = AVURLAsset.assetWithURL_(video_url)
            
            # Get video duration
            duration_cmtime = asset.duration()
            duration = CMTimeGetSeconds(duration_cmtime)
            
            if duration <= 0:
                logger.error("Could not get video duration")
                return []
            
            logger.info(f"Video duration: {duration:.1f}s, extracting every {interval}s")
            
            # Create image generator
            generator = AVAssetImageGenerator.assetImageGeneratorWithAsset_(asset)
            generator.setAppliesPreferredTrackTransform_(True)  # Correct orientation
            generator.setMaximumSize_(CGSizeMake(max_width, max_height))
            generator.setRequestedTimeToleranceBefore_(CMTimeMake(1, 10))  # 0.1s tolerance
            generator.setRequestedTimeToleranceAfter_(CMTimeMake(1, 10))
            
            thumbnails = []
            current_time = 0.0
            frame_count = 0
            
            while current_time < duration:
                output_filename = f"thumb_{frame_count:04d}.jpg"
                output_path = cache_subdir / output_filename
                
                try:
                    # Create CMTime for the requested timestamp
                    time_value = int(current_time * 600)  # 600 is common timebase
                    request_time = CMTimeMake(time_value, 600)
                    
                    # Generate image
                    error = objc.nil
                    actual_time = objc.nil
                    
                    cgimage, actual_time, error = generator.copyCGImageAtTime_actualTime_error_(
                        request_time, None, None
                    )
                    
                    if cgimage is not None:
                        # Save as JPEG
                        output_url = NSURL.fileURLWithPath_(str(output_path))
                        destination = CGImageDestinationCreateWithURL(
                            output_url, UTTypeJPEG.identifier(), 1, None
                        )
                        
                        if destination:
                            # Set compression quality
                            options = {kCGImageDestinationLossyCompressionQuality: 0.7}
                            CGImageDestinationAddImage(destination, cgimage, options)
                            CGImageDestinationFinalize(destination)
                            
                            thumbnails.append((current_time, str(output_path)))
                            
                            if frame_count == 0:
                                logger.debug(f"First thumbnail extracted at {current_time}s")
                    else:
                        logger.warning(f"Failed to generate thumbnail at {current_time}s")
                        
                except Exception as e:
                    logger.warning(f"Error extracting thumbnail at {current_time}s: {e}")
                
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
                        'method': 'avfoundation',
                        'thumbnails': [(ts, Path(p).name) for ts, p in thumbnails]
                    }
                    with open(cache_meta_file, 'w') as f:
                        json.dump(meta, f)
                    logger.debug(f"Saved {len(thumbnails)} thumbnails to cache")
                except Exception as e:
                    logger.warning(f"Failed to save cache: {e}")
            
            logger.info(f"⚡ Extracted {len(thumbnails)} thumbnails using AVFoundation (native)")
            return thumbnails
            
        except Exception as e:
            logger.error(f"AVFoundation thumbnail extraction failed: {e}", exc_info=True)
            return []


def get_thumbnail_extractor():
    """
    Get the best available thumbnail extractor for the current platform.
    
    Returns AVFoundation extractor on macOS if available, otherwise FFmpeg.
    """
    if AVFoundationThumbnailExtractor.is_available():
        return AVFoundationThumbnailExtractor
    else:
        # Fallback to FFmpeg-based extractor
        from utils.video_utils import VideoThumbnailExtractor
        return VideoThumbnailExtractor


# Test function
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python avf_thumbnail.py <video_file>")
        sys.exit(1)
    
    video_file = sys.argv[1]
    
    print(f"AVFoundation available: {AVFoundationThumbnailExtractor.is_available()}")
    
    if AVFoundationThumbnailExtractor.is_available():
        thumbnails = AVFoundationThumbnailExtractor.extract_thumbnails(video_file)
        print(f"Extracted {len(thumbnails)} thumbnails")
        for ts, path in thumbnails[:5]:
            print(f"  {ts:.1f}s: {path}")
    else:
        print("AVFoundation not available on this platform")
