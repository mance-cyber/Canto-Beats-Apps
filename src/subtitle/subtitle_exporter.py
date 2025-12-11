"""
Subtitle Exporter.

Export subtitles to various formats (SRT, ASS, TXT).
"""

from typing import List, Dict
from pathlib import Path
from datetime import timedelta


class SubtitleExporter:
    """Export subtitles to various formats."""
    
    def __init__(self):
        pass
    
    def export_srt(self, segments: List[Dict], output_path: str) -> bool:
        """
        Export subtitles to SRT format.
        
        Args:
            segments: List of subtitle segments with 'start', 'end', 'text'
            output_path: Output file path
            
        Returns:
            True if successful
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, seg in enumerate(segments, 1):
                    # Sequence number
                    f.write(f"{i}\n")
                    
                    # Timecodes
                    start_time = self._format_srt_time(seg['start'])
                    end_time = self._format_srt_time(seg['end'])
                    f.write(f"{start_time} --> {end_time}\n")
                    
                    # Text
                    f.write(f"{seg['text']}\n")
                    f.write("\n")
            
            return True
        except Exception as e:
            print(f"Error exporting SRT: {e}")
            return False
    
    def export_ass(self, segments: List[Dict], output_path: str, 
                   style_name: str = "Default") -> bool:
        """
        Export subtitles to ASS (Advanced SubStation Alpha) format.
        
        Args:
            segments: List of subtitle segments
            output_path: Output file path
            style_name: Style name to use
            
        Returns:
            True if successful
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                # Write header
                f.write("[Script Info]\n")
                f.write("Title: Canto-beats Export\n")
                f.write("ScriptType: v4.00+\n")
                f.write("Collisions: Normal\n")
                f.write("PlayDepth: 0\n\n")
                
                # Write styles
                f.write("[V4+ Styles]\n")
                f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
                       "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
                       "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
                       "Alignment, MarginL, MarginR, MarginV, Encoding\n")
                f.write(f"Style: {style_name},Arial,20,&H00FFFFFF,&H000000FF,&H00000000,"
                       "&H00000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1\n\n")
                
                # Write events
                f.write("[Events]\n")
                f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
                
                for seg in segments:
                    start_time = self._format_ass_time(seg['start'])
                    end_time = self._format_ass_time(seg['end'])
                    text = seg['text'].replace('\n', '\\N')  # ASS line break
                    
                    f.write(f"Dialogue: 0,{start_time},{end_time},{style_name},,0,0,0,,{text}\n")
            
            return True
        except Exception as e:
            print(f"Error exporting ASS: {e}")
            return False
    
    def export_txt(self, segments: List[Dict], output_path: str, 
                   include_timestamps: bool = True) -> bool:
        """
        Export subtitles to plain text.
        
        Args:
            segments: List of subtitle segments
            output_path: Output file path
            include_timestamps: Whether to include timestamps
            
        Returns:
            True if successful
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for seg in segments:
                    if include_timestamps:
                        timestamp = f"[{seg['start']:.2f}s - {seg['end']:.2f}s]"
                        f.write(f"{timestamp} {seg['text']}\n")
                    else:
                        f.write(f"{seg['text']}\n")
            
            return True
        except Exception as e:
            print(f"Error exporting TXT: {e}")
            return False
    
    def _format_srt_time(self, seconds: float) -> str:
        """Format time for SRT (00:00:00,000)"""
        td = timedelta(seconds=seconds)
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        millis = int((seconds - int(seconds)) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def _format_ass_time(self, seconds: float) -> str:
        """Format time for ASS (0:00:00.00)"""
        td = timedelta(seconds=seconds)
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        centisecs = int((seconds - int(seconds)) * 100)
        
        return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"
