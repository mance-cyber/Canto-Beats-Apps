"""
License key generator tool for Canto-beats
用於生成授權序號給用戶

使用方法:
    python generate_license.py --count 10 --output licenses.txt
    python generate_license.py --trial --count 5
"""

import argparse
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from core.license_manager import LicenseGenerator


def main():
    parser = argparse.ArgumentParser(description='Canto-beats License Key Generator')
    parser.add_argument(
        '--count',
        type=int,
        default=1,
        help='Number of license keys to generate (default: 1)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='licenses.txt',
        help='Output file path (default: licenses.txt)'
    )
    parser.add_argument(
        '--trial',
        action='store_true',
        help='Generate trial licenses (7 days, default: permanent)'
    )
    parser.add_argument(
        '--transfers',
        type=int,
        default=1,
        help='Number of machine transfers allowed (default: 1)'
    )
    
    args = parser.parse_args()
    
    # Create generator
    generator = LicenseGenerator()
    
    # Generate licenses
    license_type = 'trial' if args.trial else 'permanent'
    licenses = []
    
    print(f"\n{'='*60}")
    print(f"Canto-beats License Key Generator")
    print(f"{'='*60}")
    print(f"License Type: {license_type.upper()}")
    print(f"Transfers Allowed: {args.transfers}")
    print(f"Count: {args.count}")
    print(f"{'='*60}\n")
    
    for i in range(args.count):
        key = generator.generate(
            license_type=license_type,
            transfers_allowed=args.transfers
        )
        licenses.append(key)
        print(f"[{i+1:03d}] {key}")
    
    # Save to file
    output_path = Path(args.output)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"Canto-beats License Keys\n")
        f.write(f"Generated: {Path(__file__).stem}\n")
        f.write(f"Type: {license_type}\n")
        f.write(f"Transfers: {args.transfers}\n")
        f.write(f"{'='*60}\n\n")
        
        for i, key in enumerate(licenses, 1):
            f.write(f"{i:03d}. {key}\n")
    
    print(f"\n{'='*60}")
    print(f"✅ {args.count} license keys saved to: {output_path.absolute()}")
    print(f"{'='*60}\n")
    
    # Show usage instructions
    print("使用說明:")
    print("1. 將序號分發給用戶")
    print("2. 用戶在首次啟動 Canto-beats 時輸入序號")
    print("3. 序號將綁定到用戶的機器")
    print(f"4. 每個序號可轉移 {args.transfers} 次\n")


if __name__ == "__main__":
    main()
