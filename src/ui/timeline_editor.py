"""
Timeline Editor widget for subtitle visualization and editing.
"""

import math
import bisect
from typing import List, Dict, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QSizePolicy, 
    QMenu, QInputDialog, QApplication, QHBoxLayout,
    QLabel, QFrame, QToolTip
)
from PySide6.QtCore import Qt, Signal, QPoint, QRect, QSize, QRectF
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QMouseEvent, 
    QAction, QCursor, QFont, QFontMetrics, QWheelEvent,
    QLinearGradient, QPainterPath, QIcon
)
import os

from ui.timeline_config import Colors, Dimensions, ZOOM_LEVELS, DEFAULT_ZOOM_INDEX
from ui.edit_history import EditHistory
from core.path_setup import get_icon_path

class TimeRuler(QWidget):
    """
    Ruler widget displaying time markers.
    """
    
    seek_requested = Signal(float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(Dimensions.RULER_HEIGHT)
        self.duration = 0.0
        self.pixels_per_second = ZOOM_LEVELS[DEFAULT_ZOOM_INDEX]
        self.offset = 0
        
    def set_duration(self, duration: float):
        self.duration = duration
        self.update_width()
        self.update()
        
    def set_zoom(self, pixels_per_second: int):
        self.pixels_per_second = pixels_per_second
        self.update_width()
        self.update()
        
    def update_width(self):
        width = int(self.duration * self.pixels_per_second)
        # Ensure minimum width to fill parent
        if self.parent():
            width = max(width, self.parent().width())
        self.setFixedWidth(width)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Colors.RULER_BG)
        
        # Determine visible range for optimization
        visible_rect = event.rect()
        start_pixel = visible_rect.left()
        end_pixel = visible_rect.right()
        
        start_sec = start_pixel / self.pixels_per_second
        end_sec = end_pixel / self.pixels_per_second
        
        # Calculate grid spacing based on zoom level
        # We want a major tick roughly every 100 pixels
        target_pixel_step = 100
        raw_step = target_pixel_step / self.pixels_per_second
        
        # Find nice step size (1, 2, 5, 10, 30, 60, etc.)
        steps = [1, 2, 5, 10, 15, 30, 60, 120, 300, 600]
        step_sec = steps[0]
        for s in steps:
            if s >= raw_step:
                step_sec = s
                break
        
        # Draw ticks
        painter.setPen(Colors.RULER_TEXT)
        painter.setFont(QFont("Arial", 8))
        
        first_tick = math.floor(start_sec / step_sec) * step_sec
        last_tick = math.ceil(end_sec / step_sec) * step_sec
        
        current_sec = first_tick
        while current_sec <= last_tick:
            x = int(current_sec * self.pixels_per_second)
            
            # Major tick
            painter.setPen(Colors.RULER_MARKER)
            painter.drawLine(x, 15, x, self.height())
            
            # Text
            time_str = self._format_time(current_sec)
            painter.setPen(Colors.RULER_TEXT)
            painter.drawText(x + 4, 25, time_str)
            
            # Minor ticks
            minor_step = step_sec / 5
            if minor_step * self.pixels_per_second > 10: # Only draw if enough space
                for i in range(1, 5):
                    minor_sec = current_sec + i * minor_step
                    mx = int(minor_sec * self.pixels_per_second)
                    if mx > end_pixel: break
                    painter.setPen(Colors.RULER_MARKER)
                    painter.drawLine(mx, 22, mx, self.height())
            
            current_sec += step_sec
            
    def mousePressEvent(self, event):
        """Handle mouse clicks to seek"""
        if event.button() == Qt.LeftButton:
            # Calculate time from click position
            time = event.pos().x() / self.pixels_per_second
            # Emit signal directly
            self.seek_requested.emit(time)
            event.accept()
        else:
            super().mousePressEvent(event)
            
    def _format_time(self, seconds: float) -> str:
        """Format time as HH:MM:SS (Figma style)"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        return f"{h:02d}:{m:02d}:{s:02d}"
        


class TimelineTrack(QWidget):
    """
    The actual track widget where segments are drawn.
    """
    
    # Signals
    seek_requested = Signal(float)
    segment_edited = Signal(int, str)  # index, new_text
    selection_changed = Signal(int)  # selected_index (-1 if none)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(Dimensions.TRACK_HEIGHT)
        self.duration = 0.0
        self.pixels_per_second = ZOOM_LEVELS[DEFAULT_ZOOM_INDEX]
        self.segments = []
        self.current_time = 0.0
        self.hover_segment_index = -1
        self.selected_segment_index = -1
        self.waveform_data = [] # List of amplitude values (0.0 - 1.0)
        
        self.setMouseTracking(True)
        
    def set_duration(self, duration: float):
        self.duration = duration
        self.update_width()
        self.update()
        
    def set_zoom(self, pixels_per_second: int):
        self.pixels_per_second = pixels_per_second
        self.update_width()
        self.update()
        
    def set_segments(self, segments: List[Dict]):
        self.segments = segments
        self.update()
        
    def set_waveform(self, data: List[float]):
        """Set waveform amplitude data"""
        self.waveform_data = data
        self.update()
        
    def update_width(self):
        width = int(self.duration * self.pixels_per_second)
        if self.parent():
            width = max(width, self.parent().width())
        self.setFixedWidth(width)
        
    def get_segment_at_time(self, time: float) -> int:
        """Find segment index at given time using binary search."""
        if not self.segments:
            return -1
            
        # Binary search for the insertion point
        # We use 'start' time for sorting
        starts = [s['start'] for s in self.segments]
        idx = bisect.bisect_right(starts, time) - 1
        
        if idx >= 0:
            seg = self.segments[idx]
            if seg['start'] <= time <= seg['end']:
                return idx
                
        return -1
        
    def get_visible_segment_indices(self, start_time: float, end_time: float) -> tuple[int, int]:
        """Get range of segment indices visible within time range."""
        if not self.segments:
            return 0, 0
            
        starts = [s['start'] for s in self.segments]
        
        # Find first segment that ends after start_time
        # Optimization: Just find first segment starting after start_time - max_segment_duration
        # For simplicity and correctness, we search for start_time and look back one if needed
        start_idx = bisect.bisect_right(starts, start_time) - 1
        if start_idx < 0: start_idx = 0
        
        # Find last segment that starts before end_time
        end_idx = bisect.bisect_left(starts, end_time)
        if end_idx >= len(self.segments): end_idx = len(self.segments) - 1
        
        # Adjust to ensure we cover overlaps
        return start_idx, end_idx + 1

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), Colors.TRACK_BG)
        
        # Draw grid lines (aligned with ruler)
        painter.setPen(Colors.GRID_LINE)
        
        visible_rect = event.rect()
        start_pixel = visible_rect.left()
        end_pixel = visible_rect.right()
        
        start_sec = start_pixel / self.pixels_per_second
        end_sec = end_pixel / self.pixels_per_second
        
        # Draw grid
        grid_start = int(start_sec)
        grid_end = int(end_sec) + 1
        
        for s in range(grid_start, grid_end + 1):
            x = int(s * self.pixels_per_second)
            painter.drawLine(x, 0, x, self.height())
            
        # Draw waveform
        if len(self.waveform_data) > 0:
            self._draw_waveform(painter, start_sec, end_sec)
                
        # Draw segments
        # Optimized rendering using binary search
        start_idx, end_idx = self.get_visible_segment_indices(start_sec, end_sec)
        
        font = QFont("Microsoft YaHei", 9)
        painter.setFont(font)
        
        for i in range(start_idx, min(end_idx + 1, len(self.segments))):
            seg = self.segments[i]
            
            # Double check visibility (needed because binary search is approximate on ends)
            if seg['end'] < start_sec or seg['start'] > end_sec:
                continue
                
            start_x = int(seg['start'] * self.pixels_per_second)
            end_x = int(seg['end'] * self.pixels_per_second)
            width = max(Dimensions.MIN_SEGMENT_WIDTH, end_x - start_x)
            
            rect = QRectF(start_x, Dimensions.SEGMENT_TOP_MARGIN, width, Dimensions.SEGMENT_HEIGHT)
            
            # Determine colors
            if i == self.selected_segment_index:
                bg_color = Colors.SEGMENT_SELECTED
                border_color = Colors.SEGMENT_SELECTED.lighter(120)
            elif i == self.hover_segment_index:
                bg_color = Colors.SEGMENT_HOVER
                border_color = Colors.SEGMENT_BORDER
            else:
                bg_color = Colors.SEGMENT_DEFAULT
                border_color = Colors.SEGMENT_BORDER
                
            # Draw segment background with gradient
            grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
            grad.setColorAt(0, bg_color.lighter(110))
            grad.setColorAt(1, bg_color)
            
            path = QPainterPath()
            path.addRoundedRect(rect, 4, 4)
            
            painter.fillPath(path, grad)
            painter.setPen(QPen(border_color, 1))
            painter.drawPath(path)
            
            # Draw text
            painter.setPen(Colors.TEXT_PRIMARY)
            text_rect = rect.adjusted(5, 5, -5, -5)
            
            text = seg.get('text', '')
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, text)
            
            # Draw duration label (small, bottom right)
            duration = seg['end'] - seg['start']
            dur_text = f"{duration:.1f}s"
            painter.setPen(Colors.TEXT_SECONDARY)
            font_small = QFont("Arial", 7)
            painter.setFont(font_small)
            painter.drawText(text_rect, Qt.AlignRight | Qt.AlignBottom, dur_text)
            painter.setFont(font) # Restore font
            
        # Draw playhead
        if hasattr(self, 'current_time'):
            x = int(self.current_time * self.pixels_per_second)
            painter.setPen(QPen(Colors.PLAYHEAD, 2))
            painter.drawLine(x, 0, x, self.height())
            
            # Draw head
            painter.setBrush(QBrush(Colors.PLAYHEAD))
            painter.setPen(Qt.NoPen)
            painter.drawPolygon([
                QPoint(x-6, 0), QPoint(x+6, 0), QPoint(x, 12)
            ])
            
    def _draw_waveform(self, painter: QPainter, start_sec: float, end_sec: float):
        """Draw audio waveform"""
        if not self.waveform_data:
            return
            
        # Waveform settings
        points_per_sec = 50 # Must match extraction
        mid_y = self.height() / 2
        max_height = (self.height() - 20) / 2 # Leave some margin
        
        # Calculate index range
        start_idx = int(start_sec * points_per_sec)
        end_idx = int(end_sec * points_per_sec) + 1
        
        # Clamp indices
        start_idx = max(0, start_idx)
        end_idx = min(len(self.waveform_data), end_idx)
        
        if start_idx >= end_idx:
            return
            
        painter.setPen(Colors.WAVEFORM)
        painter.setBrush(Colors.WAVEFORM)
        
        # Draw vertical lines for each point (simple visualization)
        # For better performance at high zoom, we could use QPainterPath
        
        # Calculate pixel step per data point
        pixel_step = self.pixels_per_second / points_per_sec
        
        for i in range(start_idx, end_idx):
            amp = self.waveform_data[i]
            if amp < 0.01: continue # Skip silence
            
            x = int(i * pixel_step)
            h = int(amp * max_height)
            
            # Draw mirrored bar
            painter.drawLine(x, int(mid_y - h), x, int(mid_y + h))
            
    def mouseMoveEvent(self, event):
        pos = event.pos()
        time = pos.x() / self.pixels_per_second
        
        # Check hover using optimized search
        old_hover = self.hover_segment_index
        
        # Only check if mouse is within vertical segment area
        if Dimensions.SEGMENT_TOP_MARGIN <= pos.y() <= (Dimensions.SEGMENT_TOP_MARGIN + Dimensions.SEGMENT_HEIGHT):
            self.hover_segment_index = self.get_segment_at_time(time)
        else:
            self.hover_segment_index = -1
                
        if self.hover_segment_index != -1:
            self.setCursor(Qt.PointingHandCursor)
            # Show tooltip
            seg = self.segments[self.hover_segment_index]
            QToolTip.showText(event.globalPos(), 
                              f"[{seg['start']:.2f}s - {seg['end']:.2f}s]\n{seg.get('text', '')}")
        else:
            self.setCursor(Qt.ArrowCursor)
            QToolTip.hideText()
            
        if old_hover != self.hover_segment_index:
            self.update()
            
        super().mouseMoveEvent(event)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            time = pos.x() / self.pixels_per_second
            
            # Always seek to clicked position
            self.seek_requested.emit(time)
            self.current_time = time
            
            # Check selection
            old_selected = self.selected_segment_index
            self.selected_segment_index = self.hover_segment_index
            
            if old_selected != self.selected_segment_index:
                self.update()
                self.selection_changed.emit(self.selected_segment_index)
                
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton and self.hover_segment_index != -1:
            self.edit_segment(self.hover_segment_index)
            
    def contextMenuEvent(self, event):
        if self.hover_segment_index != -1:
            menu = QMenu(self)
            edit_action = menu.addAction("編輯文字")
            copy_action = menu.addAction("複製文字")
            
            action = menu.exec(event.globalPos())
            
            if action == edit_action:
                self.edit_segment(self.hover_segment_index)
            elif action == copy_action:
                self.copy_segment_text(self.hover_segment_index)
        

                
    def edit_segment(self, index):
        seg = self.segments[index]
        text = seg.get('text', '')
        time_range = f"{seg['start']:.1f}s - {seg['end']:.1f}s"
        
        new_text, ok = QInputDialog.getMultiLineText(
            self, "編輯字幕", 
            f"時間: {time_range}\n請輸入字幕內容:", 
            text
        )
        
        if ok and new_text != text:
            self.segments[index]['text'] = new_text
            self.update()
            self.segment_edited.emit(index, new_text)
            
    def copy_segment_text(self, index):
        text = self.segments[index].get('text', '')
        clipboard = QApplication.clipboard()
        clipboard.setText(text)


class TimelineEditor(QWidget):
    """
    Main timeline editor widget containing the ruler, track and controls.
    """
    
    seek_requested = Signal(float)
    segment_edited = Signal(int, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.zoom_index = DEFAULT_ZOOM_INDEX
        self.current_playhead_time = 0.0  # Track playhead position
        
        # Initialize edit history
        self.edit_history = EditHistory()
        self.edit_history.history_changed.connect(self._on_history_changed)
        
        self._init_ui()
        
    def set_playhead_position(self, time: float):
        """Update playhead position and auto-scroll if needed"""
        self.current_playhead_time = time
        
        # Update tracks
        self.subtitle_track.current_time = time
        self.video_track.current_time = time
        self.waveform_track.current_time = time
        
        self.subtitle_track.update()
        self.video_track.update()
        self.waveform_track.update()
        
        # Auto-scroll
        self.ensure_visible(time)
        
    def ensure_visible(self, time: float):
        """Ensure the given time is visible in the scroll area"""
        pixels_per_second = ZOOM_LEVELS[self.zoom_index]
        x = int(time * pixels_per_second)
        
        scroll_bar = self.scroll_area.horizontalScrollBar()
        current_scroll = scroll_bar.value()
        viewport_width = self.scroll_area.viewport().width()
        
        # Define a margin (e.g., 50 pixels) to trigger scroll before it hits the edge
        margin = 50
        
        if x < current_scroll + margin or x > current_scroll + viewport_width - margin:
            # Scroll to center the playhead
            target_scroll = x - (viewport_width // 2)
            scroll_bar.setValue(target_scroll)
            
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Create Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)
        
        # Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Container for Ruler + Tracks
        container = QWidget()
        container.setObjectName("timelineContainer")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        container_layout.setAlignment(Qt.AlignTop) # Ensure tracks stick to top
        
        # Ruler
        self.ruler = TimeRuler()
        self.ruler.seek_requested.connect(self._on_seek_requested)
        container_layout.addWidget(self.ruler)
        
        # Three tracks: Subtitle, Video, Waveform
        from ui.timeline_tracks import SubtitleTrack, VideoTrack, WaveformTrack
        
        # Subtitle Track
        self.subtitle_track = SubtitleTrack()
        self.subtitle_track.seek_requested.connect(self._on_seek_requested)
        self.subtitle_track.segment_edited.connect(self.segment_edited)
        self.subtitle_track.selection_changed.connect(self._on_selection_changed)
        # Connect history event directly to edit history
        self.subtitle_track.history_event.connect(
            lambda op, data: self.edit_history.add_operation(op, data)
        )
        container_layout.addWidget(self.subtitle_track)
        
        # Video Track
        self.video_track = VideoTrack()
        self.video_track.seek_requested.connect(self._on_seek_requested)
        container_layout.addWidget(self.video_track)
        
        # Waveform Track
        self.waveform_track = WaveformTrack()
        self.waveform_track.seek_requested.connect(self._on_seek_requested)
        container_layout.addWidget(self.waveform_track)
        
        # Keep legacy track reference for compatibility
        self.track = self.subtitle_track
        
        # Calculate total fixed height
        total_height = (Dimensions.RULER_HEIGHT + 
                       Dimensions.SUBTITLE_TRACK_HEIGHT + 
                       Dimensions.VIDEO_TRACK_HEIGHT + 
                       Dimensions.WAVEFORM_TRACK_HEIGHT)
        
        container.setFixedHeight(total_height)
        
        self.scroll_area.setWidget(container)
        
        # Set fixed height for the scroll area itself to match content + scrollbar
        # We add a bit of padding for the horizontal scrollbar
        self.scroll_area.setFixedHeight(total_height + 20)
        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        layout.addWidget(self.scroll_area)
        
    def _on_seek_requested(self, time: float):
        """Handle seek request from ruler or track"""
        # Update playhead position for all tracks
        self.subtitle_track.current_time = time
        self.video_track.current_time = time
        self.waveform_track.current_time = time
        
        self.subtitle_track.update()
        self.video_track.update()
        self.waveform_track.update()
        
        # Forward signal to main window
        self.seek_requested.emit(time)
    
    def _create_toolbar(self) -> QWidget:
        """Create timeline editing toolbar matching Figma design"""
        from PySide6.QtWidgets import QToolButton, QSlider, QPushButton
        
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(8)
        
        def create_icon_button(icon_name, tooltip="", enabled=True):
            btn = QToolButton()
            icon_path = get_icon_path(icon_name)
            if os.path.exists(icon_path):
                btn.setIcon(QIcon(icon_path))
                btn.setIconSize(QSize(16, 16))
            else:
                btn.setText(icon_name)
            btn.setObjectName("toolbarButton")
            btn.setToolTip(tooltip)
            btn.setEnabled(enabled)
            # Add stylesheet for disabled state
            btn.setStyleSheet("""
                QToolButton {
                    background: transparent;
                    border: none;
                    padding: 4px;
                    border-radius: 4px;
                }
                QToolButton:hover:enabled {
                    background: rgba(100, 116, 139, 0.3);
                }
                QToolButton:pressed:enabled {
                    background: rgba(100, 116, 139, 0.5);
                }
                QToolButton:disabled {
                    opacity: 0.4;
                }
            """)
            return btn
        
        # Left group: Edit tools
        # Undo
        self.undo_btn = create_icon_button("undo", "撤銷 (Ctrl+Z)", False)
        self.undo_btn.clicked.connect(self._undo)
        toolbar_layout.addWidget(self.undo_btn)
        
        # Redo
        self.redo_btn = create_icon_button("redo", "重做 (Ctrl+Y)", False)
        self.redo_btn.clicked.connect(self._redo)
        toolbar_layout.addWidget(self.redo_btn)
        
        # Separator
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.VLine)
        separator1.setStyleSheet("background-color: #475569; max-width: 1px;")
        separator1.setMaximumHeight(24)
        toolbar_layout.addWidget(separator1)
        
        # Cut/Split
        self.cut_btn = create_icon_button("scissors", "分割字幕", False)
        self.cut_btn.clicked.connect(self._split_subtitle_at_playhead)
        toolbar_layout.addWidget(self.cut_btn)
        

        
        # Delete
        self.delete_btn = create_icon_button("trash", "刪除選中字幕 (Delete)", False)
        self.delete_btn.clicked.connect(self._delete_selected_subtitle)
        toolbar_layout.addWidget(self.delete_btn)
        
        toolbar_layout.addStretch()
        
        # Right group: Add & Zoom controls
        # Add subtitle button
        self.add_btn = QPushButton(" 添加字幕")
        plus_icon_path = get_icon_path("plus")
        if os.path.exists(plus_icon_path):
            self.add_btn.setIcon(QIcon(plus_icon_path))
            self.add_btn.setIconSize(QSize(16, 16))
        self.add_btn.setObjectName("toolbarButton")
        self.add_btn.setToolTip("在當前位置添加新字幕")
        self.add_btn.clicked.connect(self._add_subtitle_at_playhead)
        toolbar_layout.addWidget(self.add_btn)
        
        # Zoom out
        self.zoom_out_btn = create_icon_button("minus", "縮小")
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        toolbar_layout.addWidget(self.zoom_out_btn)
        
        # Zoom slider
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setMinimum(0)
        self.zoom_slider.setMaximum(len(ZOOM_LEVELS) - 1)
        self.zoom_slider.setValue(self.zoom_index)
        self.zoom_slider.setFixedWidth(120)
        self.zoom_slider.setToolTip("縮放時間軸")
        self.zoom_slider.valueChanged.connect(self._on_zoom_slider_changed)
        toolbar_layout.addWidget(self.zoom_slider)
        
        # Zoom in
        self.zoom_in_btn = create_icon_button("plus", "放大")
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        toolbar_layout.addWidget(self.zoom_in_btn)
        
        # Zoom level label
        self.zoom_label = QLabel(f"{ZOOM_LEVELS[self.zoom_index]}px/s")
        self.zoom_label.setStyleSheet("color: #94a3b8; font-size: 11px; min-width: 50px;")
        toolbar_layout.addWidget(self.zoom_label)
        
        return toolbar
    
    def _on_zoom_slider_changed(self, value: int):
        """Handle zoom slider value change"""
        self.zoom_index = value
        self.update_zoom()
    
    def _add_subtitle_at_playhead(self):
        """Add new subtitle at current playhead position"""
        current_time = self.track.current_time
        
        # Create new segment (3 seconds duration by default)
        new_segment = {
            'start': current_time,
            'end': current_time + 3.0,
            'text': '新字幕'
        }
        
        # Find insertion position
        segments = self.track.segments
        insert_pos = 0
        for i, seg in enumerate(segments):
            if seg['start'] > current_time:
                break
            insert_pos = i + 1
        
        # Record operation for undo
        self.edit_history.add_operation('add', {
            'index': insert_pos,
            'segment': new_segment.copy()
        })
        
        # Insert new segment
        segments.insert(insert_pos, new_segment)
        self.track.set_segments(segments)
        self.track.selected_segment_index = insert_pos
        
        # Emit edit signal to update main window
        self.segment_edited.emit(insert_pos, new_segment['text'])
        
        # Open edit dialog immediately
        self.track.edit_segment(insert_pos)

    def _delete_selected_subtitle(self):
        """Delete currently selected subtitle"""
        if self.track.selected_segment_index >= 0:
            segments = self.track.segments
            if 0 <= self.track.selected_segment_index < len(segments):
                deleted_index = self.track.selected_segment_index
                deleted_segment = segments[deleted_index].copy()
                
                # Record operation for undo
                self.edit_history.add_operation('delete', {
                    'index': deleted_index,
                    'segment': deleted_segment
                })
                
                segments.pop(deleted_index)
                self.track.selected_segment_index = -1
                self.track.set_segments(segments)
                
                # Emit signal to update main window
                # We emit with negative index to signal deletion
                self.segment_edited.emit(-1, "")

    def _copy_selected_subtitle(self):
        """Copy selected subtitle to clipboard"""
        if self.track.selected_segment_index >= 0:
            self.track.copy_segment_text(self.track.selected_segment_index)
    def _on_selection_changed(self, index: int):
        """Update toolbar buttons based on selection"""
        has_selection = index >= 0
        self.delete_btn.setEnabled(has_selection)
        self.cut_btn.setEnabled(has_selection)
        

        
    def load_audio(self, audio_path: str, duration: float):
        """Load audio and generate waveform"""
        self.duration = duration
        self.ruler.set_duration(duration)
        self.subtitle_track.set_duration(duration)
        self.video_track.set_duration(duration)
        self.waveform_track.set_duration(duration)
        self.update_zoom()
        
        # Extract waveform data
        try:
            from utils.audio_utils import AudioPreprocessor
            print(f"Extracting waveform from {audio_path}...")
            waveform_data = AudioPreprocessor.extract_waveform_data(audio_path)
            print(f"Setting waveform data ({len(waveform_data)} points)...")
            self.waveform_track.set_waveform(waveform_data)
        except Exception as e:
            print(f"Error loading waveform: {e}")
    
    def load_video(self, video_path: str):
        """Load video and extract thumbnails with automatic method selection.

        On macOS with PyObjC: Uses AVFoundation (fastest, native hardware decode)
        Otherwise: Falls back to FFmpeg with VideoToolbox/CUDA acceleration
        """
        try:
            from utils.logger import setup_logger
            logger = setup_logger()

            logger.info(f"[Timeline] Starting thumbnail extraction for: {video_path}")

            # 直接使用 FFmpeg（更穩定）
            from utils.video_utils import VideoThumbnailExtractor
            extractor = VideoThumbnailExtractor
            extractor_name = "FFmpeg"
            logger.info("[Timeline] Using FFmpeg for thumbnails")

            thumbnails = extractor.extract_thumbnails(
                video_path,
                interval=5,
                use_cache=True
            )

            logger.info(f"[Timeline] Extracted {len(thumbnails)} thumbnails using {extractor_name}")

            if len(thumbnails) == 0:
                logger.warning("[Timeline] No thumbnails extracted!")

            self.video_track.set_thumbnails(thumbnails)
        except Exception as e:
            from utils.logger import setup_logger
            logger = setup_logger()
            logger.error(f"[Timeline] Error loading video thumbnails: {e}", exc_info=True)
    
    def set_segments(self, segments: List[Dict]):
        """Set subtitle segments to display on timeline"""
        self.subtitle_track.set_segments(segments)
        
    def wheelEvent(self, event: QWheelEvent):
        # Zoom: Ctrl or Alt + Scroll
        modifiers = event.modifiers()
        if modifiers & Qt.ControlModifier or modifiers & Qt.AltModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        # Horizontal Scroll: No modifier (Standard for timelines)
        elif modifiers == Qt.NoModifier:
            # Convert vertical scroll to horizontal scroll
            delta = event.angleDelta().y()
            scroll_bar = self.scroll_area.horizontalScrollBar()
            # Standard scroll step is usually 120 per notch, map to reasonable pixel scroll
            scroll_step = 40 
            if delta > 0:
                scroll_bar.setValue(scroll_bar.value() - scroll_step)
            else:
                scroll_bar.setValue(scroll_bar.value() + scroll_step)
            event.accept()
        else:
            super().wheelEvent(event)
            
    def zoom_in(self):
        if self.zoom_index < len(ZOOM_LEVELS) - 1:
            self.zoom_index += 1
            self.update_zoom()
            
    def zoom_out(self):
        if self.zoom_index > 0:
            self.zoom_index -= 1
            self.update_zoom()
            
    def update_zoom(self):
        pixels = ZOOM_LEVELS[self.zoom_index]
        self.zoom_label.setText(f"Zoom: {pixels}px/s")
        self.ruler.set_zoom(pixels)
        self.subtitle_track.set_zoom(pixels)
        self.video_track.set_zoom(pixels)
        self.waveform_track.set_zoom(pixels)
    
    # ==== Edit History Methods ====
    
    def undo(self):
        """Public alias for undo"""
        self._undo()
        
    def redo(self):
        """Public alias for redo"""
        self._redo()
    
    def _on_history_changed(self):
        """Update button states when history changes"""
        self.undo_btn.setEnabled(self.edit_history.can_undo())
        self.redo_btn.setEnabled(self.edit_history.can_redo())
    
    def _undo(self):
        """Undo last operation"""
        operation = self.edit_history.undo()
        if not operation:
            return
            
        # Apply reverse operation
        if operation.op_type == 'add':
            # Remove the added subtitle
            self.track.segments.pop(operation.data['index'])
        elif operation.op_type == 'delete':
            # Restore the deleted subtitle
            self.track.segments.insert(operation.data['index'], operation.data['segment'])
        elif operation.op_type == 'edit':
            # Restore old text
            self.track.segments[operation.data['index']]['text'] = operation.data['old_text']
        elif operation.op_type == 'split':
            # Merge back: remove the two split subtitles and restore original
            original_idx = operation.data['original_index']
            self.track.segments.pop(original_idx + 1)  # Remove second part
            self.track.segments.pop(original_idx)  # Remove first part
            self.track.segments.insert(original_idx, operation.data['original_segment'])
        elif operation.op_type == 'move':
            # Restore old timing
            idx = operation.data['index']
            self.track.segments[idx]['start'] = operation.data['old_start']
            self.track.segments[idx]['end'] = operation.data['old_end']
            
        self.track.set_segments(self.track.segments)
        
    def _redo(self):
        """Redo last undone operation"""
        operation = self.edit_history.redo()
        if not operation:
            return
            
        # Re-apply operation
        if operation.op_type == 'add':
            # Re-add the subtitle
            self.track.segments.insert(operation.data['index'], operation.data['segment'])
        elif operation.op_type == 'delete':
            # Re-delete the subtitle
            self.track.segments.pop(operation.data['index'])
        elif operation.op_type == 'edit':
            # Re-apply new text
            self.track.segments[operation.data['index']]['text'] = operation.data['new_text']
        elif operation.op_type == 'split':
            # Re-split
            original_idx = operation.data['original_index']
            self.track.segments.pop(original_idx)
            self.track.segments.insert(original_idx, operation.data['part1'])
            self.track.segments.insert(original_idx + 1, operation.data['part2'])
        elif operation.op_type == 'move':
            # Re-apply new timing
            idx = operation.data['index']
            self.track.segments[idx]['start'] = operation.data['new_start']
            self.track.segments[idx]['end'] = operation.data['new_end']
            
        self.track.set_segments(self.track.segments)
    
    # ==== Editing Operations ====
    
    def _split_subtitle_at_playhead(self):
        """Split subtitle at current playhead position"""
        from PySide6.QtWidgets import QMessageBox
        
        if not hasattr(self.track, 'current_time') or self.track.current_time is None:
            QMessageBox.warning(self, "無法分割", "請先設置播放位置")
            return
            
        playhead_time = self.track.current_time
        
        # Find subtitle at playhead
        subtitle_idx = None
        for i, segment in enumerate(self.track.segments):
            start = segment['start']
            end = segment['end']
            text = segment.get('text', '')
            if start <= playhead_time <= end:
                subtitle_idx = i
                break
        
        if subtitle_idx is None:
            QMessageBox.warning(self, "無法分割", "當前位置沒有字幕")
            return
        
        original_segment = self.track.segments[subtitle_idx]
        start = original_segment['start']
        end = original_segment['end']
        text = original_segment.get('text', '')
        
        # Check minimum duration
        if (playhead_time - start) < 0.5 or (end - playhead_time) < 0.5:
            QMessageBox.warning(self, "無法分割", "分割後每段至少需要 0.5 秒")
            return
        
        # Split text at approximately half or at last space before split point
        text_ratio = (playhead_time - start) / (end - start)
        split_pos = int(len(text) * text_ratio)
        
        # Try to split at word boundary (space)
        for i in range(split_pos, max(0, split_pos - 10), -1):
            if i < len(text) and text[i] == ' ':
                split_pos = i
                break
        
        text1 = text[:split_pos].strip()
        text2 = text[split_pos:].strip()
        
        # Create two new segments
        part1 = {'start': start, 'end': playhead_time, 'text': text1 if text1 else "..."}
        part2 = {'start': playhead_time, 'end': end, 'text': text2 if text2 else "..."}
        
        # Record operation for undo
        self.edit_history.add_operation('split', {
            'original_index': subtitle_idx,
            'original_segment': original_segment,
            'part1': part1,
            'part2': part2
        })
        
        # Apply split
        self.track.segments.pop(subtitle_idx)
        self.track.segments.insert(subtitle_idx, part1)
        self.track.segments.insert(subtitle_idx + 1, part2)
        
        self.track.set_segments(self.track.segments)
        
    def _show_move_dialog(self):
        """Show dialog to move selected subtitle"""
        from PySide6.QtWidgets import QMessageBox, QInputDialog
        
        selected_idx = self.track.selected_segment_index
        if selected_idx < 0 or selected_idx >= len(self.track.segments):
            QMessageBox.warning(self, "無法移動", "請先選擇一個字幕")
            return
        
        # Simple implementation: ask for time shift in seconds
        value, ok = QInputDialog.getDouble(
            self,
            "移動字幕",
            "輸入時間偏移（秒）\n正數向後移動，負數向前移動:",
            0.0,  # default
            -60.0,  # min
            60.0,  # max
            1  # decimals
        )
        
        if not ok:
            return
        
        segment = self.track.segments[selected_idx]
        old_start, old_end = segment['start'], segment['end']
        new_start = max(0, old_start + value)
        new_end = old_end + value
        
        # Check for overlaps with adjacent subtitles
        for i, other_segment in enumerate(self.track.segments):
            if i == selected_idx:
                continue
            other_start, other_end = other_segment['start'], other_segment['end']
            
            # Check if new timing overlaps
            if not (new_end <= other_start or new_start >= other_end):
                QMessageBox.warning(self, "無法移動", "移動後會與其他字幕重疊")
                return
        
        # Record operation for undo
        self.edit_history.add_operation('move', {
            'index': selected_idx,
            'old_start': old_start,
            'old_end': old_end,
            'new_start': new_start,
            'new_end': new_end
        })
        
        # Apply move
        self.track.segments[selected_idx]['start'] = new_start
        self.track.segments[selected_idx]['end'] = new_end
        
        self.track.set_segments(self.track.segments)
