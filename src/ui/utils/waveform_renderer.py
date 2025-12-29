"""
Waveform Renderer utility.

Generates visual waveform data from audio files for the Timeline Editor.
"""

import numpy as np
from pathlib import Path
from typing import Optional, List, Tuple
from PIL import Image, ImageDraw

from PySide6.QtGui import QPixmap, QImage, QColor
from PySide6.QtCore import QObject, Signal, QThread

from utils.audio_utils import AudioPreprocessor
from utils.logger import setup_logger

logger = setup_logger()


class WaveformWorker(QThread):
    """Worker thread to generate waveform image"""
    
    finished = Signal(QPixmap)
    
    def __init__(self, audio_path: str, width: int, height: int, color: str = "#007acc"):
        super().__init__()
        self.audio_path = audio_path
        self.width = width
        self.height = height
        self.color = color
        
    def run(self):
        try:
            pixmap = WaveformRenderer.generate_waveform_pixmap(
                self.audio_path, self.width, self.height, self.color
            )
            self.finished.emit(pixmap)
        except Exception as e:
            logger.error(f"Waveform generation failed: {e}")


class WaveformRenderer:
    """
    Renders audio waveforms to images/pixmaps.
    """
    
    @staticmethod
    def generate_waveform_pixmap(
        audio_path: str, 
        width: int, 
        height: int, 
        color: str = "#007acc"
    ) -> QPixmap:
        """
        Generate a QPixmap of the waveform.
        """
        # Load audio
        waveform, sr = AudioPreprocessor.load_audio(audio_path, target_sr=8000)
        
        # Convert tensor to numpy
        samples = waveform.numpy()
        
        # Downsample to fit width
        # We need 'width' number of points
        samples_per_pixel = len(samples) // width
        if samples_per_pixel < 1:
            samples_per_pixel = 1
            
        # Reshape to (width, samples_per_pixel) roughly
        # This is a simplified min/max extraction
        
        # Create image using PIL
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Parse color
        c = QColor(color)
        fill_color = (c.red(), c.green(), c.blue(), 200)
        
        mid_y = height // 2
        
        # Efficient downsampling: take max absolute value in each chunk
        # This is faster than full processing
        chunks = np.array_split(np.abs(samples), width)
        
        for x, chunk in enumerate(chunks):
            if len(chunk) == 0: continue
            
            val = np.max(chunk)
            bar_height = int(val * height * 0.9)  # 90% scale
            if bar_height < 1: bar_height = 1
            
            y1 = mid_y - (bar_height // 2)
            y2 = mid_y + (bar_height // 2)
            
            draw.line([(x, y1), (x, y2)], fill=fill_color, width=1)
            
        # Convert PIL to QImage
        data = img.tobytes("raw", "RGBA")
        qim = QImage(data, width, height, QImage.Format_RGBA8888)
        
        return QPixmap.fromImage(qim)
