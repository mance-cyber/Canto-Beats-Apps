
import os
import xml.etree.ElementTree as ET
from src.subtitle.subtitle_exporter import SubtitleExporter

def test_fcpxml_structure():
    exporter = SubtitleExporter()
    segments = [
        {'start': 0.0, 'end': 2.0, 'text': '測試字幕 1'},
        {'start': 2.5, 'end': 4.5, 'text': '測試字幕 2'}
    ]
    output_path = "test_output.fcpxml"
    
    print(f"Generating FCPXML to {output_path}...")
    success = exporter.export_fcpxml(segments, output_path)
    
    if not success:
        print("❌ Export failed!")
        return

    print("✅ Export successful. Validating structure...")
    
    try:
        tree = ET.parse(output_path)
        root = tree.getroot()
        
        # 1. Check root
        if root.tag != 'fcpxml':
            print(f"❌ Root tag is {root.tag}, expected 'fcpxml'")
            return
            
        # 2. Find spine
        spine = root.find(".//spine")
        if spine is None:
            print("❌ Could not find <spine> element")
            return
            
        # 3. Check for illegal 'caption' elements in spine
        captions = spine.findall("caption")
        if captions:
            print(f"❌ Found {len(captions)} illegal <caption > elements in <spine >!")
            for cap in captions:
                print(f"   Illegal element: {cap.tag}")
        else:
            print("✅ No <caption > elements found in <spine >.")
            
        # 4. Check for 'title' elements in spine
        titles = spine.findall("title")
        if not titles:
            print("❌ No <title > elements found in <spine >")
        else:
            print(f"✅ Found {len(titles)} <title > elements in <spine >.")
            for i, title in enumerate(titles):
                # Find the text-style that has actual text (the one with the ref attribute)
                text_styles = title.findall(".//text/text-style")
                content_style = next((ts for ts in text_styles if ts.get('ref')), None)
                text_val = content_style.text if content_style is not None else "MISSING"
                print(f"   Title {i+1}: name='{title.get('name')}', offset='{title.get('offset')}', text='{text_val}'")

        # 5. Verify text-style-def and id match
        for i, title in enumerate(titles, 1):
            text_elem = title.find("text")
            style_def = text_elem.find("text-style-def")
            style_ref = text_elem.find("text-style")
            
            if style_def is None or style_ref is None:
                print(f"❌ Missing style def or ref in Title {i}")
                continue
                
            def_id = style_def.get("id")
            ref_id = style_ref.get("ref")
            
            if def_id == ref_id:
                print(f"   ✅ Title {i} style mapping correct: {def_id} == {ref_id}")
            else:
                print(f"   ❌ Title {i} style mapping mismatch: {def_id} != {ref_id}")

    except Exception as e:
        print(f"❌ XML Parsing error: {e}")
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)

if __name__ == "__main__":
    test_fcpxml_structure()
