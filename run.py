#!/usr/bin/env python3
"""
Simple runner script for Pinterest Duplicate Detector
"""
import subprocess
import sys
import time
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import torch
        import transformers
        import faiss
        import streamlit
        import fastapi
        import uvicorn
        print("✅ All dependencies found!")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install requirements: pip install -r requirements.txt")
        return False

def generate_data():
    """Generate sample data if not exists"""
    data_file = Path("data/raw_pins.json")
    if not data_file.exists():
        print("📊 Generating sample data...")
        subprocess.run([sys.executable, "scripts/data_collection.py"])
    else:
        print("✅ Sample data already exists")

def run_api():
    """Run the FastAPI backend"""
    print("🚀 Starting API server...")
    subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "app.api:app", 
        "--host", "0.0.0.0", 
        "--port", "8000", 
        "--reload"
    ])

def run_streamlit():
    """Run the Streamlit interface"""
    print("🎨 Starting Streamlit interface...")
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", 
        "app/streamlit_ui.py", 
        "--server.port", "8501"
    ])

def main():
    """Main runner function"""
    print("🔍 Pinterest Duplicate Detector")
    print("=" * 40)
    
    if not check_dependencies():
        return
    
    generate_data()
    
    print("\nChoose what to run:")
    print("1. API only (FastAPI backend)")
    print("2. Streamlit only (Web interface)")
    print("3. Test models")
    print("4. Quick demo")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        run_api()
    elif choice == "2":
        run_streamlit()
    elif choice == "3":
        print("🧪 Testing models...")
        subprocess.run([sys.executable, "-c", "import models.embedding_extractor, models.duplicate_detector, models.quality_ranker; print('✅ All models work!')"])
        subprocess.run([sys.executable, "models/duplicate_detector.py"])
    elif choice == "4":
        print("🎯 Running quick demo...")
        print("\n1. Testing duplicate detection...")
        subprocess.run([sys.executable, "models/duplicate_detector.py"])
        
        print("\n2. Testing quality ranking...")
        subprocess.run([sys.executable, "models/quality_ranker.py"])
        
        print("\n✅ Demo complete!")
    else:
        print("Invalid choice. Please run again.")

if __name__ == "__main__":
    main()