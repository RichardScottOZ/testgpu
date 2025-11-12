#!/usr/bin/env python3
"""
Verification script to test GPU_INSCY installation on Ubuntu.
This script checks if all dependencies are installed and basic imports work.
"""

import sys
import os

def check_imports():
    """Check if all required Python packages can be imported."""
    print("Checking Python package imports...")
    required_packages = {
        'torch': 'PyTorch',
        'numpy': 'NumPy',
        'ninja': 'Ninja build system',
        'pandas': 'Pandas',
        'matplotlib': 'Matplotlib',
        'sklearn': 'scikit-learn'
    }
    
    failed = []
    for package, name in required_packages.items():
        try:
            __import__(package)
            print(f"  ✓ {name} imported successfully")
        except ImportError as e:
            print(f"  ✗ {name} import failed: {e}")
            failed.append(name)
    
    if failed:
        print(f"\n❌ Failed to import: {', '.join(failed)}")
        return False
    
    print("\n✓ All required packages imported successfully!")
    return True

def check_torch_cuda():
    """Check PyTorch CUDA availability."""
    print("\nChecking PyTorch CUDA support...")
    import torch
    
    print(f"  PyTorch version: {torch.__version__}")
    cuda_available = torch.cuda.is_available()
    
    if cuda_available:
        print(f"  ✓ CUDA is available")
        print(f"  CUDA version: {torch.version.cuda}")
        print(f"  Number of GPUs: {torch.cuda.device_count()}")
        if torch.cuda.device_count() > 0:
            print(f"  GPU 0: {torch.cuda.get_device_name(0)}")
    else:
        print(f"  ⚠ CUDA is not available (CPU-only mode)")
        print(f"  Note: GPU-accelerated functions will not work without CUDA")
    
    return True

def check_data_files():
    """Check if example data files exist."""
    print("\nChecking data files...")
    data_files = [
        'data/vowel.dat',
        'data/glass.data',
        'data/pendigits.tra'
    ]
    
    missing = []
    for data_file in data_files:
        if os.path.exists(data_file):
            size = os.path.getsize(data_file)
            print(f"  ✓ {data_file} exists ({size} bytes)")
        else:
            print(f"  ✗ {data_file} not found")
            missing.append(data_file)
    
    if missing:
        print(f"\n❌ Missing data files: {', '.join(missing)}")
        return False
    
    print("\n✓ All data files found!")
    return True

def check_source_files():
    """Check if source files exist."""
    print("\nChecking source files...")
    source_files = [
        'inscy.py',
        'inscy_map.cpp',
        'src/algorithms/GPU_INSCY.cu',
        'src/algorithms/INSCY.cpp',
        'src/structures/GPU_SCY_tree.cu',
        'src/structures/SCY_tree.cpp'
    ]
    
    missing = []
    for source_file in source_files:
        if os.path.exists(source_file):
            print(f"  ✓ {source_file} exists")
        else:
            print(f"  ✗ {source_file} not found")
            missing.append(source_file)
    
    if missing:
        print(f"\n❌ Missing source files: {', '.join(missing)}")
        return False
    
    print("\n✓ All source files found!")
    return True

def test_basic_imports():
    """Test basic functionality without compilation."""
    print("\nTesting basic data loading...")
    try:
        import torch
        import numpy as np
        
        # Test loading a small dataset
        print("  Loading vowel dataset...")
        X = torch.from_numpy(np.loadtxt("data/vowel.dat", delimiter=',', skiprows=0)).float()
        print(f"  ✓ Loaded vowel dataset: shape {X.shape}")
        
        print("  Loading glass dataset...")
        X = torch.from_numpy(np.loadtxt("data/glass.data", delimiter=',', skiprows=0)).float()
        print(f"  ✓ Loaded glass dataset: shape {X.shape}")
        
        return True
    except Exception as e:
        print(f"  ✗ Error during data loading: {e}")
        return False

def main():
    """Run all verification checks."""
    print("=" * 70)
    print("GPU_INSCY Installation Verification Script")
    print("=" * 70)
    
    results = []
    
    # Run checks
    results.append(("Package imports", check_imports()))
    results.append(("PyTorch CUDA", check_torch_cuda()))
    results.append(("Data files", check_data_files()))
    results.append(("Source files", check_source_files()))
    results.append(("Basic data loading", test_basic_imports()))
    
    # Summary
    print("\n" + "=" * 70)
    print("Verification Summary")
    print("=" * 70)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("=" * 70)
    
    if all_passed:
        print("\n🎉 All verification checks passed!")
        print("\nNext steps:")
        print("  1. Run 'python test.py' for a quick test")
        print("  2. Run 'python run_example.py' for full example (requires CUDA)")
        print("\nNote: If CUDA is not available, only CPU-based algorithms will work.")
        return 0
    else:
        print("\n❌ Some verification checks failed.")
        print("Please review the errors above and ensure all requirements are met.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
