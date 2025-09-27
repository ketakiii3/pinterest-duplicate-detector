#!/usr/bin/env python3
"""
Helper script to create files from artifact code.
Save artifact code to a file, then run this to place it correctly.
"""

import sys
from pathlib import Path

file_mappings = {
    "embedding_extractor": "models/embedding_extractor.py",
    "duplicate_detector": "models/duplicate_detector.py",
    "quality_ranker": "models/quality_ranker.py",
    "api": "app/api.py",
    "streamlit_ui": "app/streamlit_ui.py",
    "process_images": "scripts/process_images.py",
    "extract_all_embeddings": "scripts/extract_all_embeddings.py",
    "benchmark": "scripts/benchmark.py",
    "test_api": "tests/test_api.py",
    "test_models": "tests/test_models.py"
}

def show_help():
    print("📝 File Copy Helper\n")
    print("To use this helper:")
    print("1. Copy artifact code to a temporary file (e.g., temp.py)")
    print("2. Run: python copy_helper.py <key> temp.py\n")
    print("Available keys:")
    for key, path in file_mappings.items():
        print(f"  {key:20} -> {path}")

def copy_file(key, source):
    if key not in file_mappings:
        print(f"❌ Unknown key: {key}")
        show_help()
        return
    
    dest = Path(file_mappings[key])
    dest.parent.mkdir(parents=True, exist_ok=True)
    
    with open(source, 'r') as f:
        content = f.read()
    
    with open(dest, 'w') as f:
        f.write(content)
    
    print(f"✅ Copied to: {dest}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        show_help()
    else:
        copy_file(sys.argv[1], sys.argv[2])
