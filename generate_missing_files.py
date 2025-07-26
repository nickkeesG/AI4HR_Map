#!/usr/bin/env python3
"""
Generate Missing Markdown Files
Creates placeholder .md files for broken wiki links in an Obsidian vault.
"""

import os
import re
import argparse
from pathlib import Path
from typing import Set


def main():
    """Main function that handles command line arguments and orchestrates the generation."""
    parser = argparse.ArgumentParser(description='Generate missing markdown files for broken wiki links')
    parser.add_argument('vault_folder', help='Path to the Obsidian vault folder')
    
    args = parser.parse_args()
    
    vault_path = Path(args.vault_folder)
    if not vault_path.exists() or not vault_path.is_dir():
        print(f"Error: '{args.vault_folder}' is not a valid directory")
        return
    
    print(f"Scanning vault at: {vault_path}")
    
    # Find all existing markdown files
    existing_files = get_existing_files(vault_path)
    print(f"Found {len(existing_files)} existing markdown files")
    
    # Find all wiki links in the vault
    all_links = find_all_wiki_links(vault_path)
    print(f"Found {len(all_links)} unique wiki links")
    
    # Find broken links (links that don't have corresponding files)
    broken_links = all_links - existing_files
    print(f"Found {len(broken_links)} broken wiki links")
    
    if broken_links:
        generate_missing_files(broken_links)
    else:
        print("No broken links found - all wiki links have corresponding files!")


def get_existing_files(vault_path: Path) -> Set[str]:
    """
    Get set of all existing markdown file titles (without .md extension).
    
    Args:
        vault_path: Path to the vault directory
    
    Returns:
        Set of file titles (stems without extension)
    """
    existing_files = set()
    
    for md_file in vault_path.rglob("*.md"):
        # Use the filename without extension as the title
        title = md_file.stem
        existing_files.add(title)
    
    return existing_files


def find_all_wiki_links(vault_path: Path) -> Set[str]:
    """
    Find all wiki-style links [[title]] in all markdown files.
    
    Args:
        vault_path: Path to the vault directory
    
    Returns:
        Set of all unique link titles found
    """
    all_links = set()
    
    for md_file in vault_path.rglob("*.md"):
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find all wiki-style links [[title]] or [[title|display text]]
            wiki_links = re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', content)
            
            for link in wiki_links:
                all_links.add(link.strip())
                
        except Exception as e:
            print(f"Warning: Could not read {md_file}: {e}")
    
    return all_links


def generate_missing_files(broken_links: Set[str]):
    """
    Generate markdown files for broken links.
    
    Args:
        broken_links: Set of link titles that need files created
    """
    # Create the output directory
    output_dir = Path("generated markdown")
    output_dir.mkdir(exist_ok=True)
    
    print(f"Creating {len(broken_links)} missing files in '{output_dir}'...")
    
    for link_title in sorted(broken_links):
        # Create filename (sanitize for filesystem)
        filename = sanitize_filename(link_title) + ".md"
        file_path = output_dir / filename
        
        # Content is just the #person tag
        content = "#person \n"
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Created: {file_path}")
        except Exception as e:
            print(f"Error creating {file_path}: {e}")
    
    print(f"Successfully created {len(broken_links)} files in '{output_dir}'")


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a string to be safe for use as a filename.
    
    Args:
        filename: The original filename
    
    Returns:
        Sanitized filename safe for filesystem
    """
    # Replace characters that are problematic in filenames
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing whitespace and dots
    filename = filename.strip(' .')
    
    return filename


if __name__ == "__main__":
    main()