"""
AVPlayer-based video player widget for Apple Silicon.

Uses Apple's native AVPlayer for optimal performance and battery efficiency
on macOS. Provides the same interface as the mpv-based VideoPlayer.
"""

import sys
from pathlib import Path
from typing import Optional, Callable

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal, QTimer, QUrl
from PySide6.QtGui import QColor

from utils.logger import setup_logger

logger = setup_logger()

# Check for macOS
IS_MACOS = sys.platform == 'darwin'

if IS_MACOS:
    try:
        import objc
        from Foundation import NSURL, NSObject
        from AppKit import NSView
        from Quartz import CALayer
        
        # Import AVFoundation classes using objc
        AVFoundation = objc.loadBundle(
            'AVFoundation',
            globals(),
            bundle_path='/System/Library/Frameworks/AVFoundation.framework'
        )
        
        # Get the classes we need
        AVPlayer = objc.lookUpClass('AVPlayer')
        AVPlayerItem = objc.lookUpClass('AVPlayerItem')
        AVPlayerLayer = objc.lookUpClass('AVPlayerLayer')
        
        # Import CoreMedia for time handling
        CoreMedia = objc.loadBundle(
            'CoreMedia',
            globals(),
            bundle_path='/System/Library/Frameworks/CoreMedia.framework'
        )
        
        HAS_AVPLAYER = True
        logger.info("✅ AVPlayer (Apple native) is available")
    except Exception as e:
        HAS_AVPLAYER = False
        logger.warning(f"AVPlayer not available: {e}")
else:
    HAS_AVPLAYER = False
    logger.info("AVPlayer not available (not macOS)")


class AVPlayerWidget(QWidget):
    """
    Native AVPlayer video widget for macOS.
    
    Uses Apple's AVPlayer with hardware acceleration for optimal
    performance on Apple Silicon.
    """
    
    # Signals (same as VideoPlayer for compatibility)
    position_changed = Signal(float)  # Current time in seconds
    duration_changed = Signal(float)  # Total duration in seconds
    state_changed = Signal(bool)      # True = Playing, False = Paused
    video_loaded = Signal(bool)       # True = Video loaded
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.player: Optional['AVPlayer'] = None
        self.player_layer: Optional['AVPlayerLayer'] = None
        self.player_item: Optional['AVPlayerItem'] = None
        self.ns_view: Optional['NSView'] = None
        
        self.duration = 0.0
        self.is_playing = False
        self._has_video = False
        self._volume = 1.0
        self._is_muted = False
        self._is_looping = False
        
        # Subtitle overlay
        self._current_subtitle = ""
        self._subtitles = []  # List of (start, end, text)
        
        self._init_ui()
        self._init_avplayer()
        
        # Timer for position updates (~30fps)
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(33)
        self.update_timer.timeout.connect(self._update_position)
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if AVPlayer is available."""
        return HAS_AVPLAYER
    
    def _init_ui(self):
        """Initialize UI."""
        self.setStyleSheet("background-color: #000;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Video container
        self.video_container = QWidget()
        self.video_container.setStyleSheet("background-color: #000;")
        self.video_container.setMinimumHeight(100)  # Allow responsive sizing
        layout.addWidget(self.video_container)

        # Native CATextLayer for subtitle (will be created in _embed_player_layer)
        self.subtitle_layer = None
        
        # Keep Qt label as fallback (hidden by default)
        self.subtitle_label = QLabel(self.video_container)
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 28px;
                font-weight: bold;
                background-color: rgba(0, 0, 0, 0.7);
                padding: 10px 20px;
                border-radius: 6px;
            }
        """)
        self.subtitle_label.hide()
    
    def _init_avplayer(self):
        """Initialize AVPlayer."""
        if not HAS_AVPLAYER:
            logger.error("AVPlayer not available")
            return
        
        try:
            # Create AVPlayer
            self.player = AVPlayer.alloc().init()
            
            # Create player layer
            self.player_layer = AVPlayerLayer.playerLayerWithPlayer_(self.player)
            self.player_layer.setVideoGravity_("AVLayerVideoGravityResizeAspect")
            
            logger.info("🍎 AVPlayer initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AVPlayer: {e}")
    
    def _embed_player_layer(self):
        """Embed AVPlayerLayer into Qt widget after widget is shown."""
        if not self.player_layer:
            return
        
        try:
            # Get NSView from Qt widget
            win_id = int(self.video_container.winId())
            
            # Create NSView and add player layer
            from AppKit import NSView, NSFont
            from Quartz import CALayer, CATextLayer, kCAAlignmentCenter
            
            # Get the NSView from the window ID
            # This is a workaround since Qt doesn't directly expose NSView
            ns_view = objc.objc_object(c_void_p=win_id)
            self.ns_view = ns_view  # Store reference
            
            if ns_view and hasattr(ns_view, 'setWantsLayer_'):
                ns_view.setWantsLayer_(True)
                ns_view.layer().addSublayer_(self.player_layer)
                
                # Set frame
                bounds = ns_view.bounds()
                self.player_layer.setFrame_(bounds)
                
                # Create CATextLayer for subtitles (above AVPlayerLayer)
                self.subtitle_layer = CATextLayer.alloc().init()
                self.subtitle_layer.setString_("")
                self.subtitle_layer.setFontSize_(28.0)
                self.subtitle_layer.setForegroundColor_(objc.nil)  # Will set with attributed string
                self.subtitle_layer.setAlignmentMode_(kCAAlignmentCenter)
                self.subtitle_layer.setWrapped_(True)
                self.subtitle_layer.setContentsScale_(2.0)  # Retina support
                self.subtitle_layer.setBackgroundColor_(None)  # Transparent background

                # 确保字幕层在视频层之上 (zPosition 越大越靠前)
                self.subtitle_layer.setZPosition_(100.0)

                # Position at bottom center
                # Core Animation 坐标系原点在左下角，但 NSView 可能翻转
                layer_height = 60
                margin_from_bottom = 40

                # 检查视图是否翻转坐标系
                if hasattr(ns_view, 'isFlipped') and ns_view.isFlipped():
                    # 翻转坐标系：原点在左上角
                    layer_y = bounds.size.height - layer_height - margin_from_bottom
                else:
                    # 标准坐标系：原点在左下角
                    layer_y = margin_from_bottom

                self.subtitle_layer.setFrame_(((0, layer_y), (bounds.size.width, layer_height)))

                # Add subtitle layer on top of player layer
                ns_view.layer().addSublayer_(self.subtitle_layer)
                
                logger.info("AVPlayerLayer and CATextLayer embedded in Qt widget")
            else:
                logger.warning("Could not get NSView for embedding")
                
        except Exception as e:
            logger.error(f"Failed to embed player layer: {e}")
    
    def showEvent(self, event):
        """Handle show event to embed player layer."""
        super().showEvent(event)
        # Embed player layer when widget is shown
        QTimer.singleShot(100, self._embed_player_layer)
    
    def resizeEvent(self, event):
        """Handle resize to update player layer frame and subtitle position."""
        super().resizeEvent(event)

        # Update AVPlayerLayer frame
        if self.player_layer and self.ns_view:
            try:
                bounds = self.ns_view.bounds()
                self.player_layer.setFrame_(bounds)

                # Update subtitle layer position
                if self.subtitle_layer:
                    layer_height = 60
                    margin_from_bottom = 40

                    # 与 _embed_player_layer 保持一致的坐标计算
                    if hasattr(self.ns_view, 'isFlipped') and self.ns_view.isFlipped():
                        layer_y = bounds.size.height - layer_height - margin_from_bottom
                    else:
                        layer_y = margin_from_bottom

                    self.subtitle_layer.setFrame_(((0, layer_y), (bounds.size.width, layer_height)))
            except:
                pass
    
    def load_video(self, file_path: str) -> bool:
        """
        Load a video file.
        
        Args:
            file_path: Path to video file
            
        Returns:
            True if successful
        """
        if not self.player:
            logger.error("AVPlayer not initialized")
            return False
        
        file_path = Path(file_path)
        if not file_path.exists():
            logger.error(f"Video file not found: {file_path}")
            return False
        
        try:
            logger.info(f"🍎 Loading video with AVPlayer: {file_path.name}")
            
            # Clear existing subtitles when loading new video
            self._subtitles = []
            self._current_subtitle = ""
            if self.subtitle_layer:
                self.subtitle_layer.setString_("")
            
            # Create URL and player item
            url = NSURL.fileURLWithPath_(str(file_path.absolute()))
            self.player_item = AVPlayerItem.playerItemWithURL_(url)
            
            # Replace current item
            self.player.replaceCurrentItemWithPlayerItem_(self.player_item)
            
            # Wait for item to be ready
            # AVPlayerItemStatus: Unknown=0, ReadyToPlay=1, Failed=2
            import time
            for _ in range(50):  # Max 5 seconds
                status = self.player_item.status()
                if status == 1:  # ReadyToPlay
                    break
                elif status == 2:  # Failed
                    error = self.player_item.error()
                    logger.error(f"AVPlayer item failed: {error}")
                    return False
                time.sleep(0.1)
            
            # Get duration using ffprobe (more reliable than CMTime)
            try:
                import subprocess
                from core.path_setup import get_ffprobe_path
                ffprobe_path = get_ffprobe_path()
                cmd = [
                    ffprobe_path, '-v', 'quiet', '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1', str(file_path.absolute())
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and result.stdout.strip():
                    self.duration = float(result.stdout.strip())
                else:
                    self.duration = 0.0
            except Exception as e:
                logger.warning(f"FFprobe duration failed: {e}")
                self.duration = 0.0
            
            logger.info(f"⚡ Video loaded, duration: {self.duration:.1f}s")
            
            self._has_video = True
            self.duration_changed.emit(self.duration)
            self.video_loaded.emit(True)
            
            # Start paused
            self.player.pause()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load video: {e}")
            self._has_video = False
            self.video_loaded.emit(False)
            return False
    
    def play(self):
        """Start playback."""
        if self.player and self._has_video:
            self.player.play()
            self.is_playing = True
            self.state_changed.emit(True)
            self.update_timer.start()
    
    def pause(self):
        """Pause playback."""
        if self.player:
            self.player.pause()
            self.is_playing = False
            self.state_changed.emit(False)
            self.update_timer.stop()
    
    def toggle_playback(self):
        """Toggle play/pause."""
        if self.is_playing:
            self.pause()
        else:
            self.play()
    
    def seek(self, time_seconds: float):
        """
        Seek to specific time with accurate seeking.

        Args:
            time_seconds: Time in seconds
        """
        if not self.player or not self._has_video:
            return

        try:
            from CoreMedia import CMTimeMakeWithSeconds

            # Use CMTimeMakeWithSeconds for precise seeking
            seek_time = CMTimeMakeWithSeconds(time_seconds, 600)
            
            # Use accurate seeking with zero tolerance for frame-accurate results
            # This ensures the seek completes before any subsequent play command
            zero_time = CMTimeMakeWithSeconds(0, 600)
            
            # Store if we were playing before seek
            was_playing = self.is_playing
            
            # seekToTime:toleranceBefore:toleranceAfter: for accurate seeking
            self.player.seekToTime_toleranceBefore_toleranceAfter_(
                seek_time, zero_time, zero_time
            )
            
            # Update current time immediately for UI feedback
            self._last_seek_time = time_seconds
            
            # Update subtitle display immediately (especially important when paused)
            self._update_subtitle(time_seconds)
            
            logger.info(f"[AVPlayer] Seeked to {time_seconds:.2f}s (accurate)")

        except Exception as e:
            logger.error(f"[AVPlayer] Seek failed: {e}", exc_info=True)
    
    def skip(self, seconds: float):
        """Skip forward or backward."""
        if not self._has_video:
            return
        
        current = self.get_current_time()
        new_time = max(0, min(current + seconds, self.duration))
        self.seek(new_time)
    
    def get_current_time(self) -> float:
        """Get current playback time in seconds."""
        if not self.player:
            return 0.0

        try:
            from CoreMedia import CMTimeGetSeconds
            current_cmtime = self.player.currentTime()
            seconds = CMTimeGetSeconds(current_cmtime)
            return float(seconds) if seconds >= 0 else 0.0
        except Exception as e:
            logger.debug(f"[AVPlayer] get_current_time failed: {e}")
            return 0.0
    
    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)."""
        self._volume = max(0.0, min(1.0, volume))
        if self.player:
            self.player.setVolume_(self._volume)
    
    def get_volume(self) -> float:
        """Get current volume."""
        return self._volume
    
    def set_muted(self, muted: bool):
        """Set mute state."""
        self._is_muted = muted
        if self.player:
            self.player.setMuted_(muted)
    
    def is_muted(self) -> bool:
        """Check if muted."""
        return self._is_muted
    
    def set_looping(self, loop: bool):
        """Set looping mode."""
        self._is_looping = loop
        # AVPlayer looping requires notification observer
        # For now, we'll handle this in _update_position
    
    def is_looping(self) -> bool:
        """Check if looping."""
        return self._is_looping
    
    def _update_position(self):
        """Update position and check for looping."""
        if not self.player or not self._has_video:
            return
        
        current_time = self.get_current_time()
        self.position_changed.emit(current_time)
        
        # Update subtitle
        self._update_subtitle(current_time)
        
        # Handle looping
        if self._is_looping and current_time >= self.duration - 0.1:
            self.seek(0)
    
    def load_subtitle(self, file_path: str):
        """
        Load SRT subtitle file for overlay display.

        Args:
            file_path: Path to SRT file
        """
        try:
            self._subtitles = []
            logger.info(f"[Subtitle] Loading SRT file: {file_path}")

            # 检查文件是否存在
            import os
            if not os.path.exists(file_path):
                logger.error(f"[Subtitle] SRT file not found: {file_path}")
                return

            # Parse SRT file
            import pysrt
            subs = pysrt.open(file_path)

            for sub in subs:
                start = sub.start.hours * 3600 + sub.start.minutes * 60 + sub.start.seconds + sub.start.milliseconds / 1000
                end = sub.end.hours * 3600 + sub.end.minutes * 60 + sub.end.seconds + sub.end.milliseconds / 1000
                text = sub.text.replace('\n', ' ')
                self._subtitles.append((start, end, text))

            logger.info(f"[Subtitle] Loaded {len(self._subtitles)} subtitles for overlay")
            if self._subtitles:
                logger.info(f"[Subtitle] First subtitle: {self._subtitles[0]}")

            # 检查 subtitle_layer 状态
            logger.info(f"[Subtitle] subtitle_layer is None: {self.subtitle_layer is None}")
            logger.info(f"[Subtitle] ns_view is None: {self.ns_view is None}")

            # 确保 subtitle_layer 已初始化（解决时序问题）
            if self.subtitle_layer is None:
                logger.warning("[Subtitle] subtitle_layer not yet initialized, deferring refresh 500ms")
                # 延迟刷新，等待 _embed_player_layer 完成
                from PySide6.QtCore import QTimer
                QTimer.singleShot(500, self.refresh_subtitle)
            else:
                # Force refresh subtitle display at current time
                self.refresh_subtitle()

        except Exception as e:
            logger.error(f"Failed to load subtitles: {e}")
    
    def refresh_subtitle(self):
        """Force refresh subtitle display at current playback time."""
        logger.info(f"[Subtitle] refresh_subtitle called, subtitles count: {len(self._subtitles)}")
        logger.info(f"[Subtitle] subtitle_layer: {self.subtitle_layer}")
        current_time = self.get_current_time()
        # Reset current subtitle to force update
        self._current_subtitle = None  # Use None to force refresh even with same text
        self._update_subtitle(current_time)

    def _update_subtitle(self, current_time: float):
        """Update subtitle display based on current time."""
        if not self._subtitles:
            return

        # 检查 subtitle_layer 是否已初始化
        if self.subtitle_layer is None:
            return

        # Find matching subtitle
        current_text = ""
        for start, end, text in self._subtitles:
            if start <= current_time <= end:
                current_text = text
                break

        # Update CATextLayer if changed (使用 is not 处理 None 情况)
        if self._current_subtitle is None or current_text != self._current_subtitle:
            self._current_subtitle = current_text
            logger.info(f"[Subtitle] Updating subtitle at {current_time:.2f}s: '{current_text[:30] if current_text else ''}'")

            # 方案 1: 使用 Qt QLabel 作为主要字幕显示（更可靠）
            self._update_qt_subtitle_label(current_text)

            # 方案 2: 同时尝试 CATextLayer（如果可用）
            if self.subtitle_layer:
                try:
                    from AppKit import (
                        NSFont, NSColor, NSMutableAttributedString,
                        NSFontAttributeName, NSForegroundColorAttributeName,
                        NSBackgroundColorAttributeName
                    )
                    from Foundation import NSMakeRange

                    if current_text:
                        # Create attributed string with styling
                        attr_string = NSMutableAttributedString.alloc().initWithString_(current_text)
                        text_range = NSMakeRange(0, len(current_text))

                        # Set font
                        font = NSFont.boldSystemFontOfSize_(28.0)
                        attr_string.addAttribute_value_range_(NSFontAttributeName, font, text_range)

                        # Set white foreground color
                        attr_string.addAttribute_value_range_(
                            NSForegroundColorAttributeName,
                            NSColor.whiteColor(),
                            text_range
                        )

                        # Set semi-transparent black background
                        attr_string.addAttribute_value_range_(
                            NSBackgroundColorAttributeName,
                            NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 0.7),
                            text_range
                        )

                        self.subtitle_layer.setString_(attr_string)
                    else:
                        self.subtitle_layer.setString_("")
                except Exception as e:
                    logger.warning(f"CATextLayer subtitle update failed: {e}")

    def _update_qt_subtitle_label(self, text: str):
        """使用 Qt QLabel 显示字幕（备选方案，更可靠）"""
        if not hasattr(self, 'subtitle_label') or self.subtitle_label is None:
            return

        if text:
            self.subtitle_label.setText(text)
            self.subtitle_label.adjustSize()
            # 使用父控件的尺寸（可能是 video_container 或被重新设置的父控件）
            parent = self.subtitle_label.parentWidget()
            if parent:
                parent_width = parent.width()
                parent_height = parent.height()
            else:
                parent_width = self.width()
                parent_height = self.height()

            label_width = min(self.subtitle_label.sizeHint().width() + 40, parent_width - 40)
            self.subtitle_label.setFixedWidth(label_width)
            x = (parent_width - label_width) // 2
            y = parent_height - self.subtitle_label.height() - 50
            self.subtitle_label.move(x, max(0, y))
            self.subtitle_label.show()
            self.subtitle_label.raise_()  # 确保在最上层
            logger.debug(f"[Subtitle] QLabel positioned at ({x}, {y}), size: {label_width}x{self.subtitle_label.height()}")
        else:
            self.subtitle_label.hide()
    
    @property
    def has_video(self) -> bool:
        """Check if a video is loaded."""
        return self._has_video
    
    def cleanup(self):
        """Clean up resources."""
        self.update_timer.stop()
        
        if self.player:
            self.player.pause()
        
        self.player = None
        self.player_item = None
        self.player_layer = None
        
        logger.info("AVPlayer cleaned up")


def is_avplayer_available() -> bool:
    """Check if AVPlayer is available on this system."""
    return HAS_AVPLAYER


# Test function
if __name__ == "__main__":
    print(f"AVPlayer available: {is_avplayer_available()}")
    
    if is_avplayer_available():
        from PySide6.QtWidgets import QApplication
        app = QApplication([])
        
        player = AVPlayerWidget()
        player.resize(800, 600)
        player.show()
        
        # Test with a video file if provided
        import sys
        if len(sys.argv) > 1:
            player.load_video(sys.argv[1])
        
        app.exec()
