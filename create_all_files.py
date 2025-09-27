#!/usr/bin/env python3
"""
Create all project files with their complete code
Run this script to generate the entire project structure
"""

import os
from pathlib import Path

def create_file(filepath, content):
    """Create a file with given content"""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"✅ Created: {filepath}")

def main():
    print("🚀 Creating all project files...\n")
    
    # Note: Due to length limits, I'll create the essential starter files
    # You'll need to copy the full implementations from the artifacts I provided
    
    # 1. Create __init__.py files
    init_files = [
        'app/__init__.py',
        'models/__init__.py', 
        'scripts/__init__.py',
        'tests/__init__.py',
        'app/streamlit_app/__init__.py'
    ]
    
    for file in init_files:
        create_file(file, '')
    
    # 2. Create data_collection.py with minimal working version
    data_collection_code = '''import json
import random
from pathlib import Path
from datetime import datetime

def main():
    output_dir = Path("data")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pins = []
    categories = ["food", "fashion", "home-decor", "travel", "diy", "art"]
    
    # Generate 1000 sample pins
    for i in range(1000):
        pins.append({
            "pin_id": f"pin_{i:06d}",
            "title": f"Pin {i} - {random.choice(categories).title()}",
            "description": f"Description for pin {i}",
            "image_url": f"https://picsum.photos/400/600?random={i}",
            "category": random.choice(categories),
            "likes": random.randint(0, 10000),
            "saves": random.randint(0, 5000),
            "comments": random.randint(0, 500),
            "width": random.choice([400, 600, 800, 1200]),
            "height": random.choice([600, 800, 1000, 1600]),
            "source_url": f"https://example.com/pin/{i}",
            "created_at": datetime.now().isoformat(),
            "user_id": f"user_{random.randint(1, 100):03d}",
            "board_id": f"board_{random.randint(1, 50):03d}"
        })
    
    # Create duplicate clusters
    for cluster_id in range(50):
        num_duplicates = random.randint(3, 5)
        base_pin_idx = random.randint(0, len(pins) - 1)
        base_pin = pins[base_pin_idx].copy()
        
        for dup_idx in range(num_duplicates):
            dup_pin = base_pin.copy()
            dup_pin["pin_id"] = f"dup_{cluster_id}_{dup_idx}"
            dup_pin["likes"] = base_pin["likes"] + random.randint(-100, 100)
            pins.append(dup_pin)
    
    # Save
    output_path = output_dir / "raw_pins.json"
    with open(output_path, 'w') as f:
        json.dump(pins, f, indent=2)
    
    print(f"✅ Saved {len(pins)} pins to {output_path}")

if __name__ == "__main__":
    main()
'''
    create_file('scripts/data_collection.py', data_collection_code)
    
    # 3. Create a simple README with instructions
    readme_code = '''# Pinterest Duplicate Detector

## Quick Setup

You need to copy the full code from the artifacts. Here's what to do:

### Step 1: Copy Core Models
Create these files with the code from artifacts:
- `models/embedding_extractor.py` - Copy from "CLIP Embedding Extractor" artifact
- `models/duplicate_detector.py` - Copy from "Duplicate Detector with FAISS" artifact  
- `models/quality_ranker.py` - Copy from "Quality Ranking System" artifact

### Step 2: Copy Application Files
- `app/api.py` - Copy from "FastAPI Backend" artifact
- `app/streamlit_ui.py` - Copy from "Streamlit Dashboard" artifact

### Step 3: Copy Additional Scripts
- `scripts/process_images.py` - Copy from artifacts
- `scripts/extract_all_embeddings.py` - Copy from artifacts
- `scripts/benchmark.py` - Copy from artifacts

### Step 4: Copy Tests
- `tests/test_api.py` - Copy from artifacts
- `tests/test_models.py` - Copy from artifacts

### Step 5: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 6: Generate Data
```bash
python scripts/data_collection.py
```

### Step 7: Run
```bash
# Terminal 1
uvicorn app.api:app --reload

# Terminal 2  
streamlit run app/streamlit_ui.py
```
'''
    create_file('README.md', readme_code)
    
    # 4. Create requirements.txt
    requirements = '''torch>=2.0.0
transformers>=4.30.0
Pillow>=9.5.0
opencv-python>=4.8.0
numpy>=1.24.0
scipy>=1.10.0
faiss-cpu>=1.7.4
scikit-learn>=1.3.0
fastapi>=0.100.0
uvicorn>=0.23.0
pydantic>=2.0.0
python-multipart>=0.0.6
streamlit>=1.25.0
plotly>=5.15.0
pandas>=2.0.0
requests>=2.31.0
beautifulsoup4>=4.12.0
pytest>=7.4.0
pytest-cov>=4.1.0
httpx>=0.24.0
python-dotenv>=1.0.0
pyyaml>=6.0
tqdm>=4.65.0
'''
    create_file('requirements.txt', requirements)
    
    # 5. Create a helper script to copy files from clipboard
    copy_helper = '''#!/usr/bin/env python3
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
    print("📝 File Copy Helper\\n")
    print("To use this helper:")
    print("1. Copy artifact code to a temporary file (e.g., temp.py)")
    print("2. Run: python copy_helper.py <key> temp.py\\n")
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
'''
    create_file('copy_helper.py', copy_helper)
    
    print("\n" + "="*60)
    print("✅ Basic project structure created!")
    print("="*60)
    print("\n📋 NEXT STEPS:\n")
    print("1. Install dependencies:")
    print("   pip install -r requirements.txt\n")
    print("2. Generate sample data:")
    print("   python scripts/data_collection.py\n")
    print("3. Copy full implementations from artifacts:")
    print("   - Save each artifact code to a temp file")
    print("   - Use: python copy_helper.py <key> <tempfile>")
    print("   - Or manually copy to correct locations\n")
    print("4. See README.md for detailed instructions\n")

if __name__ == "__main__":
    main()