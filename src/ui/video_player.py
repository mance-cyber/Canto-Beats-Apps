"""
Video Player widget using python-mpv.
"""

import os
import sys
from typing import Optional
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QSlider, QLabel, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QTimer, Slot, QSize, QEvent
from PySide6.QtGui import QIcon, QKeySequence, QShortcut

from utils.logger import setup_logger

logger = setup_logger()

# Try to import mpv
# First, add project root to PATH to find libmpv-2.dll
try:
    project_root = Path(__file__).parent.parent.parent
    dll_path = str(project_root)
    if dll_path not in os.environ["PATH"]:
        os.environ["PATH"] = dll_path + os.pathsep + os.environ["PATH"]
        logger.info(f"Added DLL path: {dll_path}")
except Exception as e:
    logger.warning(f"Could not add DLL path: {e}")

try:
    import mpv
    HAS_MPV = True
    logger.info("libmpv loaded successfully")
except ImportError:
    HAS_MPV = False
    logger.error("python-mpv not found")
except OSError as e:
    HAS_MPV = False
    logger.error(f"libmpv not found: {e}")


class VideoPlayer(QWidget):
    """
    High-performance video player based on MPV.
    """
    
    # Signals
    position_changed = Signal(float)  # Current time in seconds
    duration_changed = Signal(float)  # Total duration in seconds
    state_changed = Signal(bool)      # True = Playing, False = Paused
    video_loaded = Signal(bool)       # True = Video loaded, False = No video

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.mpv_player: Optional[mpv.MPV] = None
        self.duration = 0.0
        self.is_playing = False
        self.is_seeking = False
        self._has_video = False
        
        self._init_ui()
        self._init_mpv()
        
        # Timer for position updates (60fps for smooth timeline)
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(16)  # ~60fps
        self.update_timer.timeout.connect(self._update_position)
        
    def _init_ui(self):
        """Initialize user interface"""
        self.setStyleSheet("""
            QWidget {
                background-color: #000;
                color: #fff;
            }
            QSlider::groove:horizontal {
                border: 1px solid #334155;
                height: 4px;
                background: #334155;
                margin: 2px 0;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #06b6d4;
                border: 2px solid white;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: #22d3ee;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #06b6d4, stop:1 #0891b2);
                border-radius: 2px;
            }
            QPushButton {
                border-radius: 4px;
                padding: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Video container
        self.video_container = QFrame()
        self.video_container.setStyleSheet("background-color: #000;")
        self.video_container.setMinimumHeight(400)
        layout.addWidget(self.video_container)
        
        # Progress slider
        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.setRange(0, 1000)
        self.seek_slider.setValue(0)
        self.seek_slider.sliderPressed.connect(self._on_slider_pressed)
        self.seek_slider.sliderReleased.connect(self._on_slider_released)
        self.seek_slider.sliderMoved.connect(self._on_slider_moved)
        layout.addWidget(self.seek_slider)
        
        # Controls
        self.controls = QFrame()
        self.controls.setObjectName("videoControlsPanel")
        self.controls.setStyleSheet("""
            QFrame#videoControlsPanel {
                background-color: rgba(15, 23, 42, 0.95);
                border-top: 1px solid #334155;
            }
        """)
        self.controls.setFixedHeight(60)
        controls_layout = QHBoxLayout(self.controls)
        controls_layout.setContentsMargins(16, 0, 16, 0)
        controls_layout.setSpacing(12)
        
        # Left group: Time display
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setObjectName("timeLabel")
        self.time_label.setStyleSheet("""
            QLabel {
                font-family: "Consolas", "Monaco", monospace;
                font-size: 16px; 
                font-weight: bold;
                color: #22d3ee;
                background-color: rgba(6, 182, 212, 0.1);
                border: 1px solid rgba(34, 211, 238, 0.3);
                border-radius: 4px;
                padding: 4px 8px;
            }
        """)
        controls_layout.addWidget(self.time_label)
        
        controls_layout.addStretch()
        
        # Helper to create icon button
        def create_icon_button(icon_name, size=20, tooltip=""):
            btn = QPushButton()
            icon_path = f"src/resources/icons/{icon_name}.svg"
            if os.path.exists(icon_path):
                btn.setIcon(QIcon(icon_path))
                btn.setIconSize(QSize(size, size))
            else:
                btn.setText(icon_name) # Fallback
            btn.setToolTip(tooltip)
            return btn


        # Center group: Playback controls
        # Skip Back 5s
        self.skip_back_btn = create_icon_button("skip-back", 20, "後退5秒")
        self.skip_back_btn.setFixedSize(36, 36)
        self.skip_back_btn.clicked.connect(lambda: self.skip(-5))
        controls_layout.addWidget(self.skip_back_btn)
        
        # Play/Pause (Same size as other buttons)
        self.play_btn = create_icon_button("play", 20, "播放/暫停 (Space)")
        self.play_btn.setObjectName("playButton")
        self.play_btn.setFixedSize(36, 36)
        self.play_btn.clicked.connect(self.toggle_playback)
        controls_layout.addWidget(self.play_btn)
        
        # Skip Forward 5s
        self.skip_forward_btn = create_icon_button("skip-forward", 20, "前進5秒")
        self.skip_forward_btn.setFixedSize(36, 36)
        self.skip_forward_btn.clicked.connect(lambda: self.skip(5))
        controls_layout.addWidget(self.skip_forward_btn)
        
        controls_layout.addStretch()
        
        # Right group: Settings
        # Volume button
        self.volume_btn = create_icon_button("volume", 20, "音量: 100% (點擊靜音 / 滾輪調整)")
        self.volume_btn.setFixedSize(36, 36)
        self.volume_btn.clicked.connect(self._toggle_mute)
        # Enable wheel event
        self.volume_btn.installEventFilter(self)
        controls_layout.addWidget(self.volume_btn)
        
        # Loop button
        self.loop_btn = create_icon_button("repeat", 20, "循環播放")
        self.loop_btn.setFixedSize(36, 36)
        self.loop_btn.setCheckable(True)
        self.loop_btn.clicked.connect(self._toggle_loop)
        controls_layout.addWidget(self.loop_btn)
        
        layout.addWidget(self.controls)

    def eventFilter(self, obj, event):
        """Handle scroll events for volume button"""
        if obj == self.volume_btn and event.type() == QEvent.Wheel:
            delta = event.angleDelta().y()
            self._adjust_volume(delta > 0)
            return True
        return super().eventFilter(obj, event)
        
    def _adjust_volume(self, increase: bool):
        """Adjust volume by 5%"""
        if not self.mpv_player:
            return
            
        current = self.mpv_player.volume or 100
        step = 5 if increase else -5
        new_vol = max(0, min(100, current + step))
        self.mpv_player.volume = new_vol
        
        # Update tooltip
        self.volume_btn.setToolTip(f"音量: {int(new_vol)}% (點擊靜音 / 滾輪調整)")
        
        # Ensure not muted if volume increased
        if increase and self.mpv_player.mute:
            self._toggle_mute()
    
    def _toggle_mute(self):
        """Toggle mute state"""
        if not self.mpv_player:
            return
        
        self.mpv_player.mute = not self.mpv_player.mute
        is_muted = self.mpv_player.mute
        
        # Update icon
        icon_name = "volume-x" if is_muted else "volume"
        icon_path = f"src/resources/icons/{icon_name}.svg"
        if os.path.exists(icon_path):
            self.volume_btn.setIcon(QIcon(icon_path))
            
        # Update style
        if is_muted:
            self.volume_btn.setStyleSheet("background-color: #ef4444; color: white;")
        else:
            self.volume_btn.setStyleSheet("")
            
    def _toggle_loop(self):
        """Toggle loop mode"""
        if not self.mpv_player:
            return
        
        is_looping = self.loop_btn.isChecked()
        self.mpv_player.loop_file = 'inf' if is_looping else 'no'
        
        # Update button style
        style = """
            background-color: #06b6d4;
            color: white;
        """ if is_looping else ""
        self.loop_btn.setStyleSheet(style)
        
    def _init_mpv(self):
        """Initialize MPV player"""
        if not HAS_MPV:
            self._show_error("MPV not available")
            return
            
        try:
            # Create MPV instance with window embedding
            self.mpv_player = mpv.MPV(
                wid=str(int(self.video_container.winId())),
                input_default_bindings=True,
                input_vo_keyboard=True,
                osc=True
            )
            
            # Configure MPV
            self.mpv_player.keep_open = True
            
            # Connect events
            @self.mpv_player.property_observer('duration')
            def on_duration(name, value):
                if value:
                    self.duration = value
                    self.duration_changed.emit(value)
                    self._update_time_label()
            
            @self.mpv_player.property_observer('time-pos')
            def on_time(name, value):
                # We use timer for UI updates, but this is good for internal state
                pass
                
            @self.mpv_player.property_observer('pause')
            def on_pause(name, value):
                self.is_playing = not value
                self.state_changed.emit(self.is_playing)
                
        except Exception as e:
            logger.error(f"Failed to initialize MPV: {e}")
            self._show_error(f"MPV Error: {e}")
            
    def _show_error(self, message):
        """Show error message in video container"""
        msg = QLabel(message)
        msg.setAlignment(Qt.AlignCenter)
        msg.setStyleSheet("color: red; font-size: 14px;")
        
        layout = self.video_container.layout()
        if not layout:
            layout = QVBoxLayout(self.video_container)
        layout.addWidget(msg)
        
    def load_video(self, file_path: str):
        """Load and play a video file"""
        if not HAS_MPV or not self.mpv_player:
            QMessageBox.warning(self, "錯誤", "MPV 播放器未初始化")
            return
            
        if not Path(file_path).exists():
            QMessageBox.warning(self, "錯誤", f"找不到檔案: {file_path}")
            return
            
        try:
            logger.info(f"Loading video: {file_path}")
            self.mpv_player.play(file_path)
            
            # Wait for file to load and get duration
            import time
            time.sleep(0.5)
            
            if self.mpv_player.duration:
                self.duration = self.mpv_player.duration
                logger.info(f"Video loaded, duration: {self.duration}s")
                self.duration_changed.emit(self.duration)
                self._has_video = True
                self.video_loaded.emit(True)
            
        except Exception as e:
            logger.error(f"Error loading video: {e}")
            QMessageBox.critical(self, "錯誤", f"無法載入影片:\n{str(e)}")
            self._has_video = False
            self.video_loaded.emit(False)
            return
        
        self.mpv_player.pause = True  # Start paused
        
        # Reset state
        self.seek_slider.setValue(0)
        self._update_time_label(0, 0)
        
    def toggle_playback(self):
        """Toggle play/pause"""
        if not self.mpv_player:
            return
            
        self.mpv_player.pause = not self.mpv_player.pause
        
        # Start/stop update timer based on play state
        if not self.mpv_player.pause:
            self.update_timer.start()
        else:
            self.update_timer.stop()
            
    def seek(self, time_seconds: float):
        """Seek to specific time"""
        if not self.mpv_player:
            return
        
        if not self._has_video:
            logger.warning("Cannot seek: no video loaded")
            return
            
        try:
            self.mpv_player.seek(time_seconds, reference="absolute", precision="exact")
        except Exception as e:
            logger.error(f"Seek error: {e}")
            # Silently ignore seek errors when no video is loaded
    
    def toggle_play(self):
        """Alias for toggle_playback (for keyboard shortcuts)"""
        self.toggle_playback()
    
    def skip(self, seconds: float):
        """Skip forward (+) or backward (-) by seconds"""
        if not self.mpv_player or not self._has_video:
            return
        
        current_time = self.mpv_player.time_pos or 0
        new_time = max(0, min(current_time + seconds, self.duration))
        self.seek(new_time)
        
    def load_subtitle(self, file_path: str):
        """Load a subtitle file"""
        if not self.mpv_player or not self._has_video:
            logger.warning("Cannot load subtitles: no video loaded")
            return
            
        try:
            logger.info(f"Loading subtitle: {file_path}")
            # Remove all existing subtitle tracks first
            # We need to collect IDs first because removing might change the list
            if hasattr(self.mpv_player, 'track_list'):
                subs_to_remove = [
                    t['id'] for t in self.mpv_player.track_list 
                    if t.get('type') == 'sub'
                ]
                
                for sub_id in subs_to_remove:
                    try:
                        self.mpv_player.sub_remove(sub_id)
                    except Exception as e:
                        logger.warning(f"Failed to remove subtitle track {sub_id}: {e}")
            else:
                # Fallback for older libmpv versions if track_list isn't available
                # But usually track_list is available in python-mpv
                try:
                    self.mpv_player.sub_remove()
                except Exception:
                    pass

            # Add new subtitle
            self.mpv_player.sub_add(file_path)
            # self.mpv_player.sub_reload() # Not needed after sub_add
            logger.info("Subtitle loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load subtitles: {e}")
            # Don't show error to user - this is called frequently during edits

    def _update_position(self):
        """Update UI based on player position"""
        if not self.mpv_player or self.is_seeking or not self._has_video:
            return
            
        current_time = self.mpv_player.time_pos or 0
        
        # Update slider without triggering seek event
        self.seek_slider.blockSignals(True)
        if self.duration > 0:
            pos = int((current_time / self.duration) * 1000)
            self.seek_slider.setValue(pos)
        self.seek_slider.blockSignals(False)
        
        self._update_time_label(current_time)
        self.position_changed.emit(current_time)
        
    def _update_time_label(self, current=None, total=None):
        """Update time label text"""
        if current is None and self.mpv_player:
            current = self.mpv_player.time_pos or 0
        if total is None:
            total = self.duration
            
        def fmt(s):
            m, s = divmod(int(s), 60)
            return f"{m:02d}:{s:02d}"
            
        self.time_label.setText(f"{fmt(current or 0)} / {fmt(total or 0)}")
        
    def _on_slider_pressed(self):
        self.is_seeking = True
        
    def _on_slider_released(self):
        self.is_seeking = False
        # Seek to final position
        if self.duration > 0:
            pos = self.seek_slider.value()
            time = (pos / 1000) * self.duration
            self.seek(time)
            
    def _on_slider_moved(self, value):
        if self.is_seeking and self.duration > 0:
            time = (value / 1000) * self.duration
            self._update_time_label(time)
    
    @property
    def has_video(self) -> bool:
        """Check if a video is currently loaded"""
        return self._has_video
