#!/usr/bin/env python3
"""
Quick test script to verify everything works
"""

import json
from pathlib import Path
import sys

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

def test_sample_data():
    """Test sample data generation"""
    print("🧪 Testing sample data generation...")
    
    try:
        from scripts.data_collection import PinDataCollector
        
        collector = PinDataCollector()
        pins = collector.simulate_pin_data(num_pins=20)
        collector.create_duplicate_clusters(num_clusters=5)
        
        print(f"✅ Generated {len(collector.pins)} sample pins")
        return True
    except Exception as e:
        print(f"❌ Sample data test failed: {e}")
        return False

def test_models():
    """Test model imports and basic functionality"""
    print("🧪 Testing model imports...")
    
    try:
        from models.embedding_extractor import EmbeddingExtractor
        from models.duplicate_detector import DuplicateDetector
        from models.quality_ranker import QualityRanker
        
        print("✅ All models imported successfully")
        
        # Test quality ranker with sample pin
        ranker = QualityRanker()
        sample_pin = {
            "pin_id": "test_001",
            "title": "Test Pin",
            "width": 600,
            "height": 900,
            "likes": 150,
            "saves": 75,
            "comments": 10,
            "source_url": "https://example.com",
            "user_id": "user_001"
        }
        
        quality_score = ranker.calculate_quality_score(sample_pin)
        print(f"✅ Quality scoring works: {quality_score.total_score:.3f}")
        
        return True
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return False

def test_duplicate_detection():
    """Test basic duplicate detection"""
    print("🧪 Testing duplicate detection...")
    
    try:
        # Run the duplicate detector demo
        from models.duplicate_detector import main as detector_main
        
        print("Running duplicate detector demo...")
        detector_main()
        print("✅ Duplicate detection test passed")
        
        return True
    except Exception as e:
        print(f"❌ Duplicate detection test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Running Quick Tests for Pinterest Duplicate Detector")
    print("=" * 60)
    
    tests = [
        ("Sample Data Generation", test_sample_data),
        ("Model Imports & Quality Scoring", test_models),
        ("Duplicate Detection", test_duplicate_detection),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        
        if test_func():
            passed += 1
            print(f"✅ {test_name}: PASSED")
        else:
            print(f"❌ {test_name}: FAILED")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your system is ready to use.")
        print("\n🚀 Next steps:")
        print("1. Open http://localhost:8501 in your browser")
        print("2. Click 'Generate Sample Data' in the sidebar")
        print("3. Run duplicate analysis with 50 pins")
        print("4. Explore the results and statistics!")
    else:
        print("⚠️ Some tests failed. Check the error messages above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)