#!/usr/bin/env python3
"""
Simple compilation test for GPU_INSCY on Ubuntu.
This script tests if the C++/CUDA code can be compiled without errors.
"""

import sys
import time

print("=" * 70)
print("GPU_INSCY Compilation Test")
print("=" * 70)
print("\nThis test will attempt to compile the C++/CUDA code.")
print("Note: This requires GCC/G++ to be installed.")
print("\nStarting compilation test...")
print("-" * 70)

try:
    # Import will trigger JIT compilation
    t0 = time.time()
    from inscy import *
    compile_time = time.time() - t0
    
    print("\n" + "=" * 70)
    print(f"✓ Compilation successful! (took {compile_time:.2f}s)")
    print("=" * 70)
    
    # Test data loading
    print("\nTesting data loading functions...")
    
    try:
        print("  Loading vowel dataset...")
        X = load_vowel()
        print(f"  ✓ Vowel dataset loaded: shape {X.shape}")
        
        print("  Loading glass dataset...")
        X = load_glass()
        print(f"  ✓ Glass dataset loaded: shape {X.shape}")
        
        print("\n✓ All data loading functions work correctly!")
        
    except Exception as e:
        print(f"\n⚠ Warning: Data loading test failed: {e}")
        print("This is not critical if compilation succeeded.")
    
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print("✓ GPU_INSCY compiled successfully on Ubuntu")
    print("✓ Module can be imported and used")
    
    import torch
    if torch.cuda.is_available():
        print("✓ CUDA is available - GPU functions should work")
    else:
        print("⚠ CUDA is not available - only CPU-based functions will work")
    
    print("\nThe GPU_INSCY implementation is ready to use!")
    print("\nTo run the full example:")
    print("  python run_example.py")
    print("\nNote: Running examples requires CUDA-capable GPU hardware.")
    print("=" * 70)
    
    sys.exit(0)
    
except Exception as e:
    print("\n" + "=" * 70)
    print("✗ Compilation failed!")
    print("=" * 70)
    print(f"\nError: {e}")
    print("\nPossible issues:")
    print("  1. Missing GCC/G++ compiler")
    print("  2. Missing build tools")
    print("  3. Incompatible CUDA version")
    print("  4. Missing dependencies")
    print("\nPlease check the SETUP.md file for installation instructions.")
    print("=" * 70)
    
    sys.exit(1)
