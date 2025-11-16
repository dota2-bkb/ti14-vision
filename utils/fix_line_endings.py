#!/usr/bin/env python3
"""
Script to fix line endings in CSV files.
Converts Windows line endings (CRLF) to Unix line endings (LF).
"""

import sys
import os

def fix_line_endings(file_path):
    """Convert Windows line endings to Unix line endings."""
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist.")
        return False
    
    try:
        # Read the file in binary mode to preserve exact content
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Convert CRLF to LF
        content = content.replace(b'\r\n', b'\n')
        
        # Write back the corrected content
        with open(file_path, 'wb') as f:
            f.write(content)
        
        print(f"Successfully fixed line endings in {file_path}")
        return True
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 fix_line_endings.py <csv_file_path>")
        print("Example: python3 fix_line_endings.py output_MOUZ/events_summary2.csv")
        sys.exit(1)
    
    file_path = sys.argv[1]
    success = fix_line_endings(file_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
