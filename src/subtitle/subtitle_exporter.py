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
    
    def export_fcpxml(self, segments: List[Dict], output_path: str, 
                       video_duration: float = None, fps: float = 30.0) -> bool:
        """
        Export subtitles to FCPXML format for Final Cut Pro.
        
        Args:
            segments: List of subtitle segments
            output_path: Output file path
            video_duration: Total video duration in seconds
            fps: Frames per second (default 30)
            
        Returns:
            True if successful
        """
        try:
            import xml.etree.ElementTree as ET
            from xml.dom import minidom
            
            # Calculate total duration
            if video_duration is None and segments:
                video_duration = max(seg['end'] for seg in segments) + 1.0
            elif video_duration is None:
                video_duration = 60.0  # Default 1 minute
            
            # Convert to frame counts
            total_frames = int(video_duration * fps)
            
            # Create root element
            fcpxml = ET.Element('fcpxml', version="1.10")
            
            # Add resources
            resources = ET.SubElement(fcpxml, 'resources')
            
            # Add format resource (required)
            ET.SubElement(resources, 'format', 
                         id="r1", 
                         name="FFVideoFormat1080p30",
                         frameDuration=f"1/{int(fps)}s",
                         width="1920", 
                         height="1080")
            
            # Add effect for titles (required for text)
            ET.SubElement(resources, 'effect', 
                         id="r2",
                         name="Basic Title",
                         uid=".../Titles.localized/Bumper:Opener.localized/Basic Title.localized/Basic Title.moti")
            
            # Create library structure
            library = ET.SubElement(fcpxml, 'library')
            event = ET.SubElement(library, 'event', name="Canto-beats 字幕匯出")
            project = ET.SubElement(event, 'project', name="字幕")
            
            # Create sequence with proper format reference
            sequence = ET.SubElement(project, 'sequence', 
                                   format="r1",
                                   duration=f"{total_frames}/{int(fps)}s",
                                   tcStart="0s",
                                   tcFormat="NDF",
                                   audioLayout="stereo",
                                   audioRate="48k")
            
            spine = ET.SubElement(sequence, 'spine')
            
            # Add each subtitle as a title element
            for i, seg in enumerate(segments, 1):
                start_frames = int(seg['start'] * fps)
                duration_frames = max(1, int((seg['end'] - seg['start']) * fps))
                
                # Create title element (valid in spine)
                title = ET.SubElement(spine, 'title',
                                     ref="r2",
                                     name=f"字幕 {i}",
                                     offset=f"{start_frames}/{int(fps)}s",
                                     duration=f"{duration_frames}/{int(fps)}s",
                                     start=f"3600s")
                
                # Add text content with styling
                text = ET.SubElement(title, 'text')
                text_style_def = ET.SubElement(text, 'text-style-def', id=f"ts{i}")
                text_style = ET.SubElement(text_style_def, 'text-style',
                                          font="PingFang TC",
                                          fontSize="60",
                                          fontColor="1 1 1 1",
                                          bold="0",
                                          alignment="center")
                
                # Add actual text content
                text_content = ET.SubElement(text, 'text-style', ref=f"ts{i}")
                text_content.text = seg['text']
            
            # Convert to pretty XML
            rough_string = ET.tostring(fcpxml, encoding='utf-8')
            reparsed = minidom.parseString(rough_string)
            pretty_xml = reparsed.toprettyxml(indent="  ", encoding='utf-8')
            
            # Write to file
            with open(output_path, 'wb') as f:
                f.write(pretty_xml)
            
            return True
        except Exception as e:
            print(f"Error exporting FCPXML: {e}")
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
