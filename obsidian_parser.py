#!/usr/bin/env python3
"""
Obsidian Vault Parser
Converts an Obsidian vault (folder of markdown files) into JSON format
containing nodes (files) and links between them.
"""

import os
import re
import json
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple


def main():
    """Main function that handles command line arguments and orchestrates the parsing."""
    parser = argparse.ArgumentParser(description='Parse Obsidian vault into JSON format')
    parser.add_argument('folder', help='Path to the folder containing markdown files')
    parser.add_argument('-o', '--output', default='vault_data.json', 
                       help='Output JSON file name (default: vault_data.json)')
    
    args = parser.parse_args()
    
    # Validate that the folder exists
    vault_path = Path(args.folder)
    if not vault_path.exists() or not vault_path.is_dir():
        print(f"Error: '{args.folder}' is not a valid directory")
        return
    
    print(f"Processing Obsidian vault at: {vault_path}")
    
    # Process the vault and get nodes and links
    nodes, links = process_vault(vault_path)
    
    # Create the final JSON structure
    vault_data = {
        "nodes": nodes,
        "links": links
    }
    
    # Write to output file
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(vault_data, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully processed {len(nodes)} files and found {len(links)} links")
    print(f"Output written to: {args.output}")


def extract_node_info(file_id: str, filename: str, content: str) -> Dict:
    """
    Extract node information from a markdown file's content.
    
    Args:
        file_id: Unique identifier for the file
        filename: Original filename
        content: Full file content
    
    Returns:
        Dictionary with id, title, tags, and content
    """
    # Title is simply the filename without extension (Obsidian-style)
    title = Path(filename).stem
    
    # Extract tags from YAML frontmatter and inline hashtags
    tags = set()
    body_content = content
    
    # Parse YAML frontmatter if present
    if content.startswith('---'):
        try:
            end_marker = content.find('\n---\n', 3)
            if end_marker != -1:
                frontmatter_text = content[3:end_marker]
                body_content = content[end_marker + 5:]
                
                # Look for tags in frontmatter
                for line in frontmatter_text.split('\n'):
                    line = line.strip()
                    if line.startswith('tags:'):
                        tags_value = line.split(':', 1)[1].strip()
                        if tags_value.startswith('[') and tags_value.endswith(']'):
                            # Parse list format: [tag1, tag2, tag3]
                            tags_str = tags_value[1:-1]
                            tags.update(tag.strip().strip('"\'') for tag in tags_str.split(',') if tag.strip())
                        else:
                            # Space-separated tags
                            tags.update(tag.strip() for tag in tags_value.split() if tag.strip())
        except Exception as e:
            print(f"Warning: Could not parse frontmatter in {filename}: {e}")
    
    # Find inline hashtags in the content
    inline_tags = re.findall(r'#([a-zA-Z0-9_/-]+)', body_content)
    tags.update(inline_tags)
    
    # Extract content only up to "(meta)" line if it exists
    content_for_json = content
    meta_index = content.find('(meta)')
    if meta_index != -1:
        # Find the start of the line containing "(meta)"
        line_start = content.rfind('\n', 0, meta_index)
        if line_start == -1:
            line_start = 0
        else:
            line_start += 1
        content_for_json = content[:line_start].rstrip()
    
    return {
        'id': file_id,
        'title': title,
        'tags': sorted(list(tags)),
        'content': content_for_json
    }


def process_vault(vault_path: Path) -> Tuple[List[Dict], List[Dict]]:
    """
    Process all markdown files in the vault and extract nodes and links.
    
    Returns:
        Tuple of (nodes, links) where:
        - nodes: List of dictionaries with file information
        - links: List of dictionaries with source/target relationships
    """
    nodes = []
    links = []
    all_files = {}  # Map of filename -> file_id for link resolution
    
    print("Discovering markdown files...")
    
    # Step 1: Find all markdown files recursively
    markdown_files = list(vault_path.rglob("*.md"))
    print(f"Found {len(markdown_files)} markdown files")
    
    # Step 2: Process each file to create nodes and collect file mappings
    for file_path in markdown_files:
        print(f"Processing: {file_path.name}")
        
        # Create unique ID from relative path (without extension)
        relative_path = file_path.relative_to(vault_path)
        file_id = str(relative_path.with_suffix(''))
        
        # Store mapping for link resolution
        filename_without_ext = file_path.stem
        all_files[filename_without_ext] = file_id
        all_files[str(relative_path)] = file_id  # Also store full relative path
        all_files[str(relative_path.with_suffix(''))] = file_id  # And without extension
        
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")
            continue
        
        # Extract node information
        node = extract_node_info(file_id, file_path.name, content)
        nodes.append(node)
    
    print(f"Created {len(nodes)} nodes")
    
    # Step 3: Extract links from all files
    print("Extracting links...")
    for file_path in markdown_files:
        relative_path = file_path.relative_to(vault_path)
        source_id = str(relative_path.with_suffix(''))
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            continue
        
        # Extract links from this file
        file_links = extract_links(source_id, content, all_files)
        links.extend(file_links)
    
    print(f"Found {len(links)} links")
    return nodes, links


def extract_links(source_id: str, content: str, all_files: Dict[str, str]) -> List[Dict]:
    """
    Extract wiki-style links [[title]] from markdown content.
    
    Args:
        source_id: ID of the source file
        content: File content to search for links
        all_files: Mapping of filenames to file IDs for link resolution
    
    Returns:
        List of link dictionaries with sourceId and targetId
    """
    links = []
    
    # Find all wiki-style links [[title]] or [[title|display text]]
    wiki_links = re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', content)
    
    for link_text in wiki_links:
        link_text = link_text.strip()
        
        # Look up the target file by title (filename without extension)
        if link_text in all_files and all_files[link_text] != source_id:
            links.append({
                'source': source_id,
                'target': all_files[link_text]
            })
    
    return links


if __name__ == "__main__":
    main()