#!/usr/bin/env python3
"""Verify installation and setup"""

def verify_imports():
    """Check if all required packages can be imported"""
    packages = [
        'torch',
        'transformers',
        'faiss',
        'fastapi',
        'streamlit',
        'numpy',
        'PIL',
        'sklearn'
    ]
    
    failed = []
    for pkg in packages:
        try:
            __import__(pkg)
            print(f"✓ {pkg}")
        except ImportError:
            failed.append(pkg)
            print(f"✗ {pkg}")
    
    if failed:
        print(f"\n❌ Failed to import: {', '.join(failed)}")
        return False
    
    print("\n✅ All packages imported successfully!")
    return True

def check_structure():
    """Check if project structure exists"""
    import os
    
    dirs = ['app', 'models', 'scripts', 'data', 'tests', 'docs']
    
    for d in dirs:
        if os.path.exists(d):
            print(f"✓ {d}/")
        else:
            print(f"✗ {d}/ (missing)")
    
    print("\n✅ Project structure verified!")

if __name__ == "__main__":
    print("🔍 Verifying Setup...\n")
    print("Checking imports:")
    verify_imports()
    print("\nChecking structure:")
    check_structure()
