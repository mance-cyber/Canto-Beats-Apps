"""
Configuration and constants for the Timeline Editor.
Matches Figma design exactly.
"""

from PySide6.QtGui import QColor

# Colors - Figma Design
class Colors:
    # Background colors
    BACKGROUND = QColor("#0f172a")  # Dark blue-gray
    TRACK_BG = QColor("#1e293b")  # Slightly lighter dark
    GRID_LINE = QColor("#334155")  # Subtle grid lines
    GRID_MAJOR = QColor("#475569")  # Major grid lines
    
    # Segment colors (Subtitle track)
    SEGMENT_DEFAULT = QColor("#334155")  # Dark gray segments
    SEGMENT_HOVER = QColor("#3f4d5f")  # Slightly lighter on hover
    SEGMENT_SELECTED = QColor("#06b6d4")  # Cyan highlight when selected
    SEGMENT_BORDER = QColor("#475569")  # Border color
    SEGMENT_TEXT = QColor("#f1f5f9")  # White text
    
    # Text colors
    TEXT_PRIMARY = QColor("#f8fafc")  # Almost white
    TEXT_SECONDARY = QColor("#94a3b8")  # Light gray (for time)
    
    # Playhead & accents
    PLAYHEAD = QColor("#06b6d4")  # Cyan playhead line
    
    # Time ruler
    RULER_BG = QColor("#1e293b")  
    RULER_TEXT = QColor("#94a3b8")
    RULER_MARKER = QColor("#334155")
    
    # Waveform
    WAVEFORM = QColor("#06b6d4")  # Cyan waveform bars
    WAVEFORM_ALT = QColor("#0891b2")  # Slightly darker cyan
    
    # Video track
    VIDEO_TRACK_BG = QColor("#151b2b")  # Darker than other tracks for distinction
    VIDEO_FRAME_MARKER = QColor("#06b6d4")  # Cyan

# Dimensions
class Dimensions:
    # Track heights (Figma design - compact proportions)
    SUBTITLE_TRACK_HEIGHT = 90   # Reduced to fit
    VIDEO_TRACK_HEIGHT = 50      # Made slightly taller for visibility
    WAVEFORM_TRACK_HEIGHT = 50   # Compact
    RULER_HEIGHT = 24
    
    # Subtitle segment dimensions
    SUBTITLE_SEGMENT_HEIGHT = 50  # Adjusted for new track height
    SUBTITLE_SEGMENT_TOP_MARGIN = 20  # Center in track
    MIN_SEGMENT_WIDTH = 20  # Minimum visible width
    
    # Legacy (for backward compatibility)
    TRACK_HEIGHT = 100
    SEGMENT_HEIGHT = 60
    SEGMENT_TOP_MARGIN = 20

# Zoom settings
ZOOM_LEVELS = [10, 25, 50, 75, 100, 150, 200, 300, 500]  # pixels per second
DEFAULT_ZOOM_INDEX = 4  # 100px/s default

