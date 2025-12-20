"""
Separate track widgets for the three-row timeline layout.
"""

from typing import List, Dict, Tuple
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal, QPoint, QRectF, QRect
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QPainterPath, QPixmap

from ui.timeline_config import Colors, Dimensions, ZOOM_LEVELS, DEFAULT_ZOOM_INDEX


class WaveformTrack(QWidget):
    """
    Track widget displaying audio waveform only.
    """
    
    seek_requested = Signal(float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(Dimensions.WAVEFORM_TRACK_HEIGHT)
        self.duration = 0.0
        self.pixels_per_second = ZOOM_LEVELS[DEFAULT_ZOOM_INDEX]
        self.waveform_data = []
        self.current_time = 0.0
        
    def set_duration(self, duration: float):
        self.duration = duration
        self.update_width()
        self.update()
        
    def set_zoom(self, pixels_per_second: int):
        self.pixels_per_second = pixels_per_second
        self.update_width()
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
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Colors.TRACK_BG)
        
        # Draw grid lines
        painter.setPen(Colors.GRID_LINE)
        visible_rect = event.rect()
        start_pixel = visible_rect.left()
        end_pixel = visible_rect.right()
        start_sec = start_pixel / self.pixels_per_second
        end_sec = end_pixel / self.pixels_per_second
        
        grid_start = int(start_sec)
        grid_end = int(end_sec) + 1
        for s in range(grid_start, grid_end + 1):
            x = int(s * self.pixels_per_second)
            painter.drawLine(x, 0, x, self.height())
        
        # Draw waveform
        if len(self.waveform_data) > 0:
            self._draw_waveform(painter, start_sec, end_sec)
        
        # Draw playhead
        if hasattr(self, 'current_time'):
            x = int(self.current_time * self.pixels_per_second)
            painter.setPen(QPen(Colors.PLAYHEAD, 2))
            painter.drawLine(x, 0, x, self.height())
            
    def _draw_waveform(self, painter: QPainter, start_sec: float, end_sec: float):
        """Draw audio waveform - Figma style vertical bars"""
        if not self.waveform_data:
            return
            
        points_per_sec = 50
        mid_y = self.height() / 2
        max_height = (self.height() - 16) / 2  # Leave more margin
        
        start_idx = int(start_sec * points_per_sec)
        end_idx = int(end_sec * points_per_sec) + 1
        start_idx = max(0, start_idx)
        end_idx = min(len(self.waveform_data), end_idx)
        
        if start_idx >= end_idx:
            return
            
        # Use QPen with width for thicker bars (Figma style)
        pen = QPen(Colors.WAVEFORM)
        pen.setWidth(2)  # 2px wide bars
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        
        pixel_step = self.pixels_per_second / points_per_sec
        
        for i in range(start_idx, end_idx):
            amp = self.waveform_data[i]
            if amp < 0.01:
                continue
            
            x = int(i * pixel_step)
            h = int(amp * max_height)
            
            # Draw vertical cyan bar from center outward
            painter.drawLine(x, int(mid_y - h), x, int(mid_y + h))
            
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            time = event.pos().x() / self.pixels_per_second
            self.seek_requested.emit(time)
            self.current_time = time
            self.update()


class VideoTrack(QWidget):
    """
    Track widget displaying video frame markers.
    """
    
    seek_requested = Signal(float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(Dimensions.VIDEO_TRACK_HEIGHT)
        self.duration = 0.0
        self.pixels_per_second = ZOOM_LEVELS[DEFAULT_ZOOM_INDEX]
        self.current_time = 0.0
        self.thumbnails = []  # List of (timestamp, QPixmap) tuples
        self.thumbnail_cache = {}  # Cache loaded pixmaps
        
    def set_duration(self, duration: float):
        self.duration = duration
        self.update_width()
        self.update()
        
    def set_zoom(self, pixels_per_second: int):
        self.pixels_per_second = pixels_per_second
        self.update_width()
        self.update()
        
    def set_thumbnails(self, thumbnails: List[Tuple[float, str]]):
        """Set video thumbnails as list of (timestamp, image_path) tuples"""
        self.thumbnails = thumbnails
        self.thumbnail_cache.clear()
        # Pre-load thumbnails
        for timestamp, image_path in thumbnails:
            if image_path not in self.thumbnail_cache:
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    self.thumbnail_cache[image_path] = pixmap
        self.update()
        
    def update_width(self):
        width = int(self.duration * self.pixels_per_second)
        if self.parent():
            width = max(width, self.parent().width())
        self.setFixedWidth(width)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Colors.VIDEO_TRACK_BG)
        
        # Draw grid lines
        painter.setPen(Colors.GRID_LINE)
        visible_rect = event.rect()
        start_pixel = visible_rect.left()
        end_pixel = visible_rect.right()
        start_sec = start_pixel / self.pixels_per_second
        end_sec = end_pixel / self.pixels_per_second
        
        grid_start = int(start_sec)
        grid_end = int(end_sec) + 1
        for s in range(grid_start, grid_end + 1):
            x = int(s * self.pixels_per_second)
            painter.drawLine(x, 0, x, self.height())
        
        # Draw thumbnails if available
        if self.thumbnails and self.thumbnail_cache:
            thumbnail_height = self.height() - 4  # Leave 2px margin top and bottom
            
            for timestamp, image_path in self.thumbnails:
                # Check if thumbnail is in visible range
                if timestamp < start_sec or timestamp > end_sec:
                    continue
                    
                x = int(timestamp * self.pixels_per_second)
                
                # Get cached pixmap
                if image_path in self.thumbnail_cache:
                    pixmap = self.thumbnail_cache[image_path]
                    
                    # Scale to a larger height first to get wider thumbnails
                    # Scale to 1.8x the track height, then crop vertically
                    target_scale_height = int(thumbnail_height * 1.8)
                    scaled_pixmap = pixmap.scaledToHeight(
                        target_scale_height, 
                        Qt.SmoothTransformation
                    )
                    
                    # Calculate crop area (center crop vertically)
                    crop_y = (scaled_pixmap.height() - thumbnail_height) // 2
                    crop_rect = QRect(0, crop_y, scaled_pixmap.width(), thumbnail_height)
                    
                    # Crop the pixmap
                    cropped_pixmap = scaled_pixmap.copy(crop_rect)
                    
                    # Draw thumbnail
                    painter.drawPixmap(
                        x, 2,  # 2px top margin
                        cropped_pixmap
                    )
                    
                    # Draw subtle border around thumbnail
                    painter.setPen(QPen(QColor("#475569"), 1))
                    painter.drawRect(x, 2, cropped_pixmap.width(), thumbnail_height)
        else:
            # Fallback: Show label and markers if no thumbnails
            from PySide6.QtGui import QFont
            painter.setPen(QColor("#475569"))
            font = QFont("Segoe UI", 8)
            painter.setFont(font)
            painter.drawText(8, self.height() // 2 + 4, "VIDEO")
            
            # Draw time markers
            for s in range(grid_start, grid_end + 1, 5):
                if s > 0:
                    x = int(s * self.pixels_per_second)
                    painter.drawLine(x, self.height() - 8, x, self.height())
        
        # Draw playhead (always on top)
        if hasattr(self, 'current_time'):
            x = int(self.current_time * self.pixels_per_second)
            pen = QPen(Colors.PLAYHEAD)
            pen.setWidth(3)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.drawLine(x, 0, x, self.height())
            
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            time = event.pos().x() / self.pixels_per_second
            self.seek_requested.emit(time)
            self.current_time = time
            self.update()


class SubtitleTrack(QWidget):
    """
    Track widget displaying subtitle segments with editing capabilities.
    """
    
    seek_requested = Signal(float)
    segment_edited = Signal(int, str)
    selection_changed = Signal(int)
    history_event = Signal(str, dict)  # op_type, data
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(Dimensions.SUBTITLE_TRACK_HEIGHT)
        self.duration = 0.0
        self.pixels_per_second = ZOOM_LEVELS[DEFAULT_ZOOM_INDEX]
        self.segments = []
        self.current_time = 0.0
        self.hover_segment_index = -1
        self.selected_segment_index = -1
        
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
        
    def update_width(self):
        width = int(self.duration * self.pixels_per_second)
        if self.parent():
            width = max(width, self.parent().width())
        self.setFixedWidth(width)
        
    def get_segment_at_time(self, time: float) -> int:
        """Find segment index at given time using binary search."""
        if not self.segments:
            return -1
            
        import bisect
        starts = [s['start'] for s in self.segments]
        idx = bisect.bisect_right(starts, time) - 1
        
        if idx >= 0:
            seg = self.segments[idx]
            if seg['start'] <= time <= seg['end']:
                return idx
                
        return -1
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), Colors.TRACK_BG)
        
        # Draw grid lines
        painter.setPen(Colors.GRID_LINE)
        visible_rect = event.rect()
        start_pixel = visible_rect.left()
        end_pixel = visible_rect.right()
        start_sec = start_pixel / self.pixels_per_second
        end_sec = end_pixel / self.pixels_per_second
        
        grid_start = int(start_sec)
        grid_end = int(end_sec) + 1
        for s in range(grid_start, grid_end + 1):
            x = int(s * self.pixels_per_second)
            painter.drawLine(x, 0, x, self.height())
        
        # Draw segments - Figma style
        from PySide6.QtGui import QFont
        font = QFont("Segoe UI", 14)  # 增大字體從 11 到 14
        font.setWeight(QFont.Medium)
        painter.setFont(font)
        
        for i, seg in enumerate(self.segments):
            if seg['end'] < start_sec or seg['start'] > end_sec:
                continue
                
            start_x = int(seg['start'] * self.pixels_per_second)
            end_x = int(seg['end'] * self.pixels_per_second)
            width = max(Dimensions.MIN_SEGMENT_WIDTH, end_x - start_x)
            
            rect = QRectF(start_x, Dimensions.SUBTITLE_SEGMENT_TOP_MARGIN, 
                         width, Dimensions.SUBTITLE_SEGMENT_HEIGHT)
            
            # Determine colors - Figma style (flat, no gradient)
            if i == self.selected_segment_index:
                bg_color = Colors.SEGMENT_SELECTED  # Cyan
                text_color = QColor("#ffffff")  # White text on cyan
            elif i == self.hover_segment_index:
                bg_color = Colors.SEGMENT_HOVER
                text_color = Colors.SEGMENT_TEXT
            else:
                bg_color = Colors.SEGMENT_DEFAULT  # Dark gray
                text_color = Colors.SEGMENT_TEXT
                
            # Draw segment with rounded corners (Figma style)
            path = QPainterPath()
            path.addRoundedRect(rect, 6, 6)  # 6px rounded corners
            
            # Fill with flat color (no gradient)
            painter.fillPath(path, QBrush(bg_color))
            painter.setPen(Qt.NoPen)
            painter.drawPath(path)
            
            # Draw text with proper color
            painter.setPen(text_color)
            text_rect = rect.adjusted(12, 8, -12, -8)  # More padding
            text = seg.get('text', '')
            
            # Draw text with eliding if too long
            metrics = painter.fontMetrics()
            elided_text = metrics.elidedText(text, Qt.ElideRight, int(text_rect.width()))
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, elided_text)
        
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
            
    def mouseMoveEvent(self, event):
        pos = event.pos()
        time = pos.x() / self.pixels_per_second
        
        # Handle dragging if active
        if self._handle_drag(pos.x(), time):
            return

        # Handle hover state updates
        self._update_hover_state(pos, time)
        super().mouseMoveEvent(event)
        
    def _handle_drag(self, x: int, time: float) -> bool:
        """Handle drag operations. Returns True if a drag events was handled."""
        if not hasattr(self, 'drag_mode') or self.drag_mode == 'none':
            return False
            
        if self.selected_segment_index == -1:
            return False
            
        seg = self.segments[self.selected_segment_index]
        
        if self.drag_mode == 'resize_left':
            # Resize start, keeping end fixed
            # Constraint: start >= 0 and start < end - min_duration
            new_start = max(0.0, min(time, seg['end'] - 0.5))
            seg['start'] = new_start
            self.update()
            
        elif self.drag_mode == 'resize_right':
            # Resize end, keeping start fixed
            # Constraint: end > start + min_duration
            new_end = max(seg['start'] + 0.5, time)
            seg['end'] = new_end
            self.update()
            
        elif self.drag_mode == 'move':
            # Move entire segment
            # Calculate delta from initial drag click
            dt = time - self.drag_start_time
            duration = self.initial_segment_state['end'] - self.initial_segment_state['start']
            
            new_start = max(0.0, self.initial_segment_state['start'] + dt)
            new_end = new_start + duration
            
            seg['start'] = new_start
            seg['end'] = new_end
            self.update()
            
        return True

    def _update_hover_state(self, pos, time):
        """Update cursor and hover index based on mouse position"""
        # Define edge threshold in pixels
        EDGE_THRESHOLD = 8
        
        # Check if hovering over effective area
        in_vertical_range = (Dimensions.SUBTITLE_SEGMENT_TOP_MARGIN <= pos.y() <= 
                           (Dimensions.SUBTITLE_SEGMENT_TOP_MARGIN + Dimensions.SUBTITLE_SEGMENT_HEIGHT))
                           
        if not in_vertical_range:
            self.hover_segment_index = -1
            self.setCursor(Qt.ArrowCursor)
            return

        # Find segment indices under cursor (fuzzy check for resizing resizing edge)
        # We need to check slightly wider range to catch the exact edge
        search_seg = self.get_segment_at_time(time)
        
        # Check edges of the specific segment we are over or near
        target_idx = -1
        cursor = Qt.ArrowCursor
        
        # Helper to check pixel distance to edges
        def check_edges(idx):
            if idx < 0 or idx >= len(self.segments): return Qt.ArrowCursor, False
            
            s = self.segments[idx]
            start_x = int(s['start'] * self.pixels_per_second)
            end_x = int(s['end'] * self.pixels_per_second)
            
            if abs(pos.x() - start_x) <= EDGE_THRESHOLD:
                return Qt.SizeHorCursor, True # Resize Left
            elif abs(pos.x() - end_x) <= EDGE_THRESHOLD:
                return Qt.SizeHorCursor, True # Resize Right
            elif start_x < pos.x() < end_x:
                return Qt.SizeAllCursor, False # Move (Body)
            return Qt.ArrowCursor, False
            
        # First check the segment strictly under time
        cursor, is_edge = check_edges(search_seg)
        target_idx = search_seg
        
        # If strict check fails, check adjacent segment edges (important for gapless segments)
        if not is_edge and cursor == Qt.ArrowCursor:
             # Check neighbors
             # ... implementation simplified, relying on get_segment_at_time usually being good enough
             pass
             
        self.hover_segment_index = target_idx
        self.setCursor(cursor)
        
        if target_idx != -1:
             # Basic tooltip
             seg = self.segments[target_idx]
             # Update tooltip only if not dragging
             if not hasattr(self, 'drag_mode') or self.drag_mode == 'none':
                 # QToolTip.showText(...) # Optional, removed to reduce spam
                 pass

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            time = pos.x() / self.pixels_per_second
            
            # Determine action based on current cursor state (set during hover)
            cursor = self.cursor().shape()
            
            if cursor == Qt.SizeHorCursor:
                # Resize
                self.selected_segment_index = self.hover_segment_index
                if self.selected_segment_index != -1:
                    seg = self.segments[self.selected_segment_index]
                    start_x = int(seg['start'] * self.pixels_per_second)
                    
                    # Distinguish left vs right based on distance
                    if abs(pos.x() - start_x) <= 8:
                        self.drag_mode = 'resize_left'
                    else:
                        self.drag_mode = 'resize_right'
                        
                    self.initial_segment_state = seg.copy()
                    
            elif cursor == Qt.SizeAllCursor:
                # Move
                self.selected_segment_index = self.hover_segment_index
                self.drag_mode = 'move'
                self.drag_start_time = time
                if self.selected_segment_index != -1:
                    self.initial_segment_state = self.segments[self.selected_segment_index].copy()
                    
            else:
                # Normal Seek / Selection
                self.drag_mode = 'none'
                self.seek_requested.emit(time)
                self.current_time = time
                
                self.selected_segment_index = self.hover_segment_index
                self.selection_changed.emit(self.selected_segment_index)
                
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if hasattr(self, 'drag_mode') and self.drag_mode != 'none':
                # Commit change
                if self.selected_segment_index != -1 and self.initial_segment_state:
                    new_seg = self.segments[self.selected_segment_index]
                    
                    # Detect if changes occurred
                    has_changed = (abs(new_seg['start'] - self.initial_segment_state['start']) > 0.001 or 
                                   abs(new_seg['end'] - self.initial_segment_state['end']) > 0.001)
                    
                    if has_changed:
                        # Logic to finalize move, e.g. resort if moved past other segments
                        self._sort_segments()
                        
                        # Emit history event FIRST so undo state is correct
                        # We treat resize as 'move' since both just change start/end
                        self.history_event.emit('move', {
                            'index': self.selected_segment_index,
                            'old_start': self.initial_segment_state['start'],
                            'old_end': self.initial_segment_state['end'],
                            'new_start': new_seg['start'],
                            'new_end': new_seg['end']
                        })
                        
                        # Emit update signal
                        self.segment_edited.emit(self.selected_segment_index, new_seg.get('text', ''))
            
            self.drag_mode = 'none'
            self.initial_segment_state = None
            super().mouseReleaseEvent(event)
            
    def _sort_segments(self):
        """Sort segments by start time and update index"""
        if self.selected_segment_index == -1: return
        
        # Remember the object to find new index
        target_seg = self.segments[self.selected_segment_index]
        self.segments.sort(key=lambda s: s['start'])
        
        # Update selection index
        try:
            self.selected_segment_index = self.segments.index(target_seg)
            self.selection_changed.emit(self.selected_segment_index)
        except ValueError:
            self.selected_segment_index = -1
                
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton and self.hover_segment_index != -1:
            self.edit_segment(self.hover_segment_index)
            
    def edit_segment(self, index):
        seg = self.segments[index]
        text = seg.get('text', '')
        time_range = f"{seg['start']:.1f}s - {seg['end']:.1f}s"
        
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QLabel
        
        # Create frameless dialog matching app design
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        dialog.setMinimumWidth(450)
        dialog.setMinimumHeight(280)
        dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f172a,
                    stop:0.5 #1e293b,
                    stop:1 #0f172a
                );
                border: 1px solid #334155;
                border-radius: 12px;
            }
            QLabel {
                color: #f8fafc;
                font-size: 14px;
                background: transparent;
            }
            QTextEdit {
                background-color: rgba(30, 41, 59, 0.5);
                color: #f1f5f9;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                font-family: "Microsoft YaHei", "PingFang TC", sans-serif;
                selection-background-color: #06b6d4;
            }
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #06b6d4,
                    stop:1 #3b82f6
                );
                border-radius: 8px;
                border: none;
                padding: 10px 24px;
                color: white;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0891b2,
                    stop:1 #2563eb
                );
            }
            QPushButton:pressed {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0e7490,
                    stop:1 #1d4ed8
                );
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Title with icon
        title_label = QLabel("✏ 編輯字幕")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #22d3ee;")
        layout.addWidget(title_label)
        
        # Time range
        time_label = QLabel(f"⏱ 時間: {time_range}")
        time_label.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 500;")
        layout.addWidget(time_label)
        
        # Text edit
        text_edit = QTextEdit()
        text_edit.setPlainText(text)
        text_edit.setMinimumHeight(120)
        layout.addWidget(text_edit)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(51, 65, 85, 0.8);
                border: 1px solid #475569;
                color: #f1f5f9;
            }
            QPushButton:hover {
                background-color: rgba(51, 65, 85, 1);
                border-color: #64748b;
            }
            QPushButton:pressed {
                background-color: rgba(30, 41, 59, 0.9);
            }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("✓ 確定")
        ok_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
        
        # Focus text edit
        text_edit.setFocus()
        text_edit.selectAll()
        
        if dialog.exec() == QDialog.Accepted:
            new_text = text_edit.toPlainText()
            if new_text != text:
                # Emit history event
                self.history_event.emit('edit', {
                    'index': index,
                    'old_text': text,
                    'new_text': new_text
                })
                
                self.segments[index]['text'] = new_text
                self.update()
                self.segment_edited.emit(index, new_text)
            
    def copy_segment_text(self, index):
        from PySide6.QtWidgets import QApplication
        text = self.segments[index].get('text', '')
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
