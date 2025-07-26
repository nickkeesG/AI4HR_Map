#!/usr/bin/env python3
"""
Script to add "(meta)" line after tags in markdown files.
The line is added after any tags (lines starting with #) but before other content.
"""

import os
import sys
import re
from pathlib import Path

def process_markdown_file(file_path):
    """Process a single markdown file to add (meta) line after tags."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not lines:
            return
        
        # Find where tags end
        tag_end_index = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('#') and not stripped.startswith('##'):  # Only single # tags
                tag_end_index = i + 1
            elif stripped == '':  # Empty line after tags
                continue
            else:  # First non-tag, non-empty line
                break
        
        # Check if (meta) already exists
        for line in lines:
            if line.strip() == '(meta)':
                print(f"Skipping {file_path} - (meta) already exists")
                return
        
        # Insert (meta) line after tags
        if tag_end_index > 0:
            # Insert after the last tag, handling empty lines appropriately
            insert_index = tag_end_index
            
            # Skip any empty lines after tags
            while insert_index < len(lines) and lines[insert_index].strip() == '':
                insert_index += 1
            
            # Insert (meta) line
            lines.insert(insert_index, '(meta)\n')
            
            # Ensure there's a blank line after (meta) if there isn't one
            if insert_index + 1 < len(lines) and lines[insert_index + 1].strip() != '':
                lines.insert(insert_index + 1, '\n')
        
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"Processed: {file_path}")
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python add_meta_line.py <folder_path>")
        sys.exit(1)
    
    folder_path = Path(sys.argv[1])
    
    if not folder_path.exists() or not folder_path.is_dir():
        print(f"Error: {folder_path} is not a valid directory")
        sys.exit(1)
    
    # Find all markdown files
    md_files = list(folder_path.glob('**/*.md'))
    
    if not md_files:
        print(f"No markdown files found in {folder_path}")
        return
    
    print(f"Found {len(md_files)} markdown files")
    
    for md_file in md_files:
        process_markdown_file(md_file)
    
    print("Done!")

if __name__ == "__main__":
    main()